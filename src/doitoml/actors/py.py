"""Declarative actions for ``doitoml``."""
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from doitoml.types import ExecutionContext
from doitoml.utils.py import make_py_function, parse_dotted_py, resolve_py_args

if TYPE_CHECKING:
    from doitoml.sources._config import ConfigSource

from ._actor import Actor

CallableAction = Callable[[], Optional[bool]]


class PyActor(Actor):

    """An actor for user-defined Python functions."""

    def knows(self, action: Dict[str, Any]) -> bool:
        """Only handles ``py`` actions."""
        if "py" not in action:
            return False
        path_dotted_func = list(action["py"].items())[0][0]
        py_path, dotted, func_name = parse_dotted_py(path_dotted_func)
        return None not in [dotted, func_name]

    def transform_action(
        self,
        source: "ConfigSource",
        action: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Expand a dict containing `py`."""
        path_dotted_func, args_kwargs = list(action["py"].items())[0]
        args, kwargs = resolve_py_args(
            self.doitoml,
            source,
            args_kwargs.pop("args", []),
            args_kwargs.pop("kwargs", {}),
        )
        args_kwargs.update(args=args, kwargs=kwargs)
        return [action]

    def perform_action(
        self,
        action: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> List[CallableAction]:
        """Build a python callable."""
        path_dotted_func, args_kwargs = list(action["py"].items())[0]

        args, kwargs = args_kwargs["args"], args_kwargs["kwargs"]
        return [
            make_py_function(path_dotted_func, args, kwargs, execution_context),
        ]
