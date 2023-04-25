"""Declarative actions for ``doitoml``."""
import abc
import contextlib
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, cast

from doitoml.errors import ActorError
from doitoml.types import LogPaths

if TYPE_CHECKING:
    from .doitoml import DoiTOML
    from .sources._config import ConfigSource

CallableAction = Callable[[], Optional[bool]]


RE_PY_DOT_FUNC = re.compile(
    r"^((?P<py_path>[^:]+?):)?((?P<dotted>[^:]+?):)((?P<func_name>[^:]+?))$",
)


class Actor:

    """A base class for a ``doitoml`` actor plugin."""

    #: a reference to the parent
    doitoml: "DoiTOML"

    #: the rank of the action
    rank = 100

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Create an Actor and remember its parent."""
        self.doitoml = doitoml

    @abc.abstractmethod
    def knows(self, action: Dict[str, Any]) -> bool:
        """Whether the actor knows how to transform and perform an action."""

    @abc.abstractmethod
    def transform_action(
        self,
        source: "ConfigSource",
        action: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Expand an action dict's tokens at the end of configuration."""

    @abc.abstractmethod
    def perform_action(
        self,
        action: Dict[str, Any],
        cwd: Path,
        env: Dict[str, str],
        log_paths: Optional[LogPaths],
        log_mode: str,
    ) -> List[CallableAction]:
        """Build a function that will fully resolve the action during task building."""


class PyActor(Actor):

    """An actor for arbitrary Python functions."""

    def _get_py_dot_func(self, py: Optional[str]) -> Tuple[Optional[str], ...]:
        if py is None:
            return None, None, None
        match = RE_PY_DOT_FUNC.search(py)
        if not match:  # pragma: no cover
            return None, None, None
        groups = match.groupdict()
        return groups.get("py_path"), groups.get("dotted"), groups.get("func_name")

    def knows(self, action: Dict[str, Any]) -> bool:
        """Only handles ``py`` actions."""
        _py_path, dotted, func_name = self._get_py_dot_func(action.get("py"))

        return None not in [dotted, func_name]

    def transform_action(
        self,
        source: "ConfigSource",
        action: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Expand a dict containing `py`."""
        args = action.pop("args", None)
        if args is None:
            return [action]

        if isinstance(args, list):
            found_args, unresolved_args = self.doitoml.config.resolve_some_path_specs(
                source,
                args,
                source_relative=False,
            )

            if unresolved_args:
                message = (
                    f"Python action {action} had unresolved positional args: "
                    f"{unresolved_args}"
                )
                raise ActorError(message)
            action["args"] = found_args
            return [action]

        if isinstance(args, dict):
            found_kwargs = {}
            unresolved_kwargs = {}

            for arg_name, arg_value in args.items():
                found_kwarg = self.resolve_one_arg(source, arg_value)
                if found_kwarg:
                    found_kwargs[arg_name] = found_kwarg
                    continue
                unresolved_kwargs[arg_name] = arg_value

            if unresolved_kwargs:
                message = (
                    f"Python action {action} had unresolved named args: "
                    f"{unresolved_kwargs}"
                )
                raise ActorError(message)
            action["args"] = found_kwargs
            return [action]

        message = f"Python action {action} had unusuable args: {args}"
        raise ActorError(message)

    def resolve_one_arg(self, source: "ConfigSource", arg_value: Any) -> Optional[Any]:
        """Resolve a single argument."""
        if isinstance(arg_value, str):
            found_kwarg = self.doitoml.config.resolve_one_path_spec(
                source,
                arg_value,
                source_relative=False,
            )
            return found_kwarg
        if isinstance(arg_value, list):
            found_kwarg = self.doitoml.config.resolve_some_path_specs(
                source,
                arg_value,
                source_relative=False,
            )[0]
            return found_kwarg
        return None

    def _patch_action_paths(
        self,
        cwd: Path,
        env: Dict[str, str],
        py_path: Optional[str] = None,
    ) -> Tuple[str, Dict[str, str], List[str]]:
        """Ensure the ``sys.path``, ``Path.cwd`` are correct: provide the old values."""
        old_env = dict(os.environ)
        os.environ.update(env)

        new_cwd = Path.cwd().resolve()
        old_cwd = str(new_cwd)

        new_cwd = Path(cwd).resolve()
        os.chdir(str(new_cwd))
        py_path = py_path or "."
        import_path = (new_cwd / py_path).resolve()
        old_sys_path = [*sys.path]
        sys.path = [str(import_path), *old_sys_path]

        return old_cwd, old_env, old_sys_path

    def _call_with_capture(
        self,
        func: Callable[[Any], Optional[bool]],
        pargs: List[Any],
        kwargs: Dict[str, Any],
        log_paths: LogPaths,
        log_mode: str,
    ) -> Optional[bool]:
        stdout, stderr = self.doitoml.ensure_parents(*log_paths)

        stdout_mgr: contextlib.AbstractContextManager = contextlib.nullcontext()
        stderr_mgr: contextlib.AbstractContextManager = contextlib.nullcontext()

        managers: List[contextlib.AbstractContextManager] = []
        if stdout:
            stdout_fh = stdout.open(log_mode)
            stdout_mgr = contextlib.redirect_stdout(stdout_fh)
            managers += [stdout_mgr]
        if stderr:
            if stderr == stdout:
                stderr_mgr = contextlib.redirect_stderr(stdout_fh)
            else:
                stderr_fh = stderr.open(log_mode)
                stderr_mgr = contextlib.redirect_stderr(stderr_fh)
            managers += [stderr_mgr]

        with stdout_mgr, stderr_mgr:
            return func(*pargs, **kwargs)

    def _init_action_args(
        self,
        action: Dict[str, Any],
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """Create positional and named arguments."""
        cfg_args = action.get("args", [])
        pargs = []
        kwargs = {}

        if isinstance(cfg_args, dict):
            kwargs = cfg_args
        elif isinstance(cfg_args, list):
            pargs = cfg_args
        else:  # pragma: no cover
            message = f"don't know what to do with action args: {cfg_args}"
            raise ActorError(message)

        return pargs, kwargs

    def _restore_action_paths(
        self,
        old_cwd: str,
        old_sys_path: List[str],
        old_env: Dict[str, str],
    ) -> None:
        """Put paths back the way they were."""
        os.chdir(str(old_cwd))
        sys.path = old_sys_path
        os.environ.clear()
        os.environ.update(old_env)

    def perform_action(
        self,
        action: Dict[str, Any],
        cwd: Path,
        env: Dict[str, str],
        log_paths: Optional[LogPaths],
        log_mode: str,
    ) -> List[CallableAction]:
        """Build a python callable."""
        py = action.get("py")
        py_path, dotted, func_name = self._get_py_dot_func(py)
        pargs, kwargs = self._init_action_args(action)

        if dotted is None or func_name is None:  # pragma: no cover
            message = f"Unknown py path: {py}"
            raise ActorError(message)

        def _py_action() -> Optional[bool]:
            """Perform a python action."""
            old_cwd, old_env, old_sys_path = self._patch_action_paths(cwd, env, py_path)

            try:
                func = self.import_dotted(str(dotted), str(func_name), cwd, py_path)
                result = self._call_with_capture(
                    func,
                    pargs,
                    kwargs,
                    cast(LogPaths, log_paths or [None, None]),
                    log_mode,
                )

            finally:  # pragma: no cover
                self._restore_action_paths(old_cwd, old_sys_path, old_env)

            return result is not False

        return [_py_action]

    def import_dotted(
        self,
        dotted: str,
        func_name: str,
        cwd: Path,
        py_path: Optional[str],
    ) -> Any:
        """Import a named function from a module."""
        if py_path and cwd:
            os.chdir(str(cwd))
        current = __import__(dotted)
        for dot in dotted.split(".")[1:]:
            current = getattr(current, dot)
        return getattr(current, func_name)
