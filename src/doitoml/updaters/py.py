"""Uptodate checkers provided by ``doit``."""
from typing import TYPE_CHECKING, Any

from doitoml.errors import ActorError
from doitoml.types import ExecutionContext, FnAction
from doitoml.utils.py import make_py_function, resolve_py_args

from ._updater import Updater

if TYPE_CHECKING:
    from doitoml.sources._config import ConfigSource


class PyUpdater(Updater):

    """A wrapper for user-defined Python functions."""

    def transform_uptodate(
        self,
        source: "ConfigSource",
        uptodate_args: Any,
    ) -> Any:
        """Update arguments for uptodate."""
        if not isinstance(uptodate_args, dict):  # pragma: no cover
            message = f"{source} provided unknown uptodate args {uptodate_args}"
            raise ActorError(message)
        path_dotted_func, args_kwargs = list(uptodate_args.items())[0]
        args, kwargs = resolve_py_args(
            self.doitoml,
            source,
            args_kwargs.pop("args", []),
            args_kwargs.pop("kwargs", {}),
        )
        args_kwargs.update(args=args, kwargs=kwargs)
        return uptodate_args

    def get_update_function(
        self,
        uptodate: Any,
        execution_context: ExecutionContext,
    ) -> FnAction:
        """Create a ``doit.tools.config_changed``."""
        path_dotted_func, args_kwargs = list(uptodate.items())[0]
        args, kwargs = args_kwargs["args"], args_kwargs["kwargs"]
        return make_py_function(
            path_dotted_func,
            args,
            kwargs,
            execution_context,
        )
