"""Declarative actions for ``doitoml``."""
import abc
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from doitoml.errors import ActorError
from doitoml.types import LogPaths
from doitoml.utils.py import make_py_function, parse_dotted_py

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
        log_paths: LogPaths,
        log_mode: str,
    ) -> List[CallableAction]:
        """Build a function that will fully resolve the action during task building."""


class PyActor(Actor):

    """An actor for arbitrary Python functions."""

    def knows(self, action: Dict[str, Any]) -> bool:
        """Only handles ``py`` actions."""
        if "py" not in action:
            return False
        py = action["py"]
        py_path, dotted, func_name = parse_dotted_py(py)
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

    def perform_action(
        self,
        action: Dict[str, Any],
        cwd: Path,
        env: Dict[str, str],
        log_paths: LogPaths,
        log_mode: str,
    ) -> List[CallableAction]:
        """Build a python callable."""
        py = action["py"]
        args, kwargs = self._init_action_args(action)
        return [make_py_function(py, args, kwargs, cwd, env, log_paths, log_mode)]
