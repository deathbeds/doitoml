"""Uptodate checkers provided by ``doit``."""
from typing import TYPE_CHECKING, Any

from doitoml.types import FnAction

from ._updater import Updater

if TYPE_CHECKING:
    from doitoml.sources._config import ConfigSource


class PyUpdater(Updater):

    """A wrapper for arbitrary python functions."""

    def transform_uptodate(
        self,
        source: "ConfigSource",
        uptodate_args: Any,
    ) -> Any:
        """Update arguments for uptodate."""
        message = f"nope {source} {uptodate_args}"
        raise NotImplementedError(message)

    def get_update_function(self, uptodate: Any) -> FnAction:
        """Create a ``doit.tools.config_changed``."""
        message = f"nope {uptodate}"
        raise NotImplementedError(message)
