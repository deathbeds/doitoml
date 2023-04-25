"""Uptodate checkers provided by ``doit``."""
from pprint import pformat
from typing import TYPE_CHECKING, Any, cast

import doit.tools

from doitoml.types import FnAction

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

    def get_update_function(self, uptodate: Any) -> FnAction:
        """Create a ``doit.tools.config_changed``."""
        return cast(FnAction, doit.tools.config_changed(uptodate))
