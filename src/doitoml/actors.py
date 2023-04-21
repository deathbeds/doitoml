"""Declarative actions for ``doitoml``."""
import abc
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from doitoml.errors import ActorError

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
        args = action.pop("args")
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

    def _fix_action_paths(
        self,
        cwd: Path,
        env: Dict[str, str],
        py_path: Optional[str] = None,
    ) -> Tuple[str, Dict[str, str], Optional[List[str]]]:
        """Ensure the ``sys.path``, ``Path.cwd`` are correct: provide the old values."""
        old_env = dict(os.environ)
        os.environ.update(env)

        old_sys_path = None
        new_cwd = Path.cwd().resolve()
        old_cwd = str(new_cwd)

        new_cwd = Path(cwd).resolve()
        os.chdir(str(new_cwd))
        py_path = py_path or "."
        import_path = (new_cwd / py_path).resolve()
        old_sys_path = [*sys.path]
        sys.path = [str(import_path), *old_sys_path]

        return old_cwd, old_env, old_sys_path

    def perform_action(
        self,
        action: Dict[str, Any],
        cwd: Path,
        env: Dict[str, str],
    ) -> List[CallableAction]:
        """Build a python callable."""
        py = action.get("py")
        py_path, dotted, func_name = self._get_py_dot_func(py)

        if dotted is None or func_name is None:  # pragma: no cover
            message = f"Unknown py path: {py}"
            raise ActorError(message)

        def _py_action() -> Optional[bool]:
            old_cwd, old_env, old_sys_path = self._fix_action_paths(cwd, env, py_path)

            try:
                current = __import__(dotted)  # type: ignore
                if py_path and cwd:
                    os.chdir(str(cwd))
                for dot in dotted.split(".")[1:]:  # type: ignore
                    current = getattr(current, dot)
                func = getattr(current, func_name)  # type: ignore
                args = action["args"]

                pargs = []
                kwargs = {}

                if isinstance(args, dict):
                    kwargs = args
                elif isinstance(args, list):
                    pargs = args
                else:  # pragma: no cover
                    message = f"don't know what to do with action args: {args}"
                    raise ActorError(message)

                result = func(*pargs, **kwargs)
            finally:  # pragma: no cover
                if old_cwd:
                    os.chdir(str(old_cwd))
                if old_sys_path:
                    sys.path = old_sys_path
                os.environ.clear()
                os.environ.update(old_env)
            return result is not False

        return [_py_action]
