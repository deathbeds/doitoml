"""Uptodate checkers provided by ``doit``."""
from pprint import pformat
from typing import TYPE_CHECKING, Any, Optional, cast

import doit.tools

from doitoml.types import ExecutionContext, FnAction

from ._updater import Updater

if TYPE_CHECKING:
    from doitoml.sources._config import ConfigSource


class ConfigChanged(Updater):

    """A wrapper for ``doit.tools.config_changed``."""

    def transform_uptodate(
        self,
        source: "ConfigSource",
        uptodate_args: Any,
    ) -> Any:
        """Update arguments for uptodate."""
        new_args = uptodate_args
        if isinstance(uptodate_args, dict):
            items = uptodate_args.items()
            new_args = pformat(
                {key: self.resolve_one_arg(source, value) for key, value in items},
            )
        if isinstance(uptodate_args, str):
            new_args = self.resolve_one_arg(source, uptodate_args)
        if isinstance(uptodate_args, list):
            new_args = [self.resolve_one_arg(source, arg) for arg in uptodate_args]
        return pformat(new_args)

    def get_update_function(
        self,
        uptodate: Any,
        execution_context: ExecutionContext,
    ) -> FnAction:
        """Create a ``doit.tools.config_changed``."""
        return cast(FnAction, doit.tools.config_changed(uptodate))

    def resolve_one_arg(self, source: "ConfigSource", arg_value: Any) -> Optional[Any]:
        """Resolve a single argument."""
        if isinstance(arg_value, str):
            return self.doitoml.config.resolve_one_path_spec(
                source,
                arg_value,
                source_relative=False,
            )
        return arg_value


class RunOnce(Updater):

    """A wrapper for ``doit.tools.run_once``."""

    def transform_uptodate(
        self,
        source: "ConfigSource",
        uptodate_args: Any,
    ) -> Any:
        """Consume any input value as ``run_once`` takes no args."""
        return None

    def get_update_function(
        self,
        uptodate: Any,
        execution_context: ExecutionContext,
    ) -> FnAction:
        """Create a ``doit.tools.run_once``."""
        return cast(FnAction, doit.tools.run_once)
