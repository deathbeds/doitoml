"""Uptodate checkers provided by ``doit``."""
from typing import TYPE_CHECKING, Any, Dict, cast

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
        uptodate: Dict[str, Any],
    ) -> Dict:
        """Update arguments for uptodate."""
        __import__("pprint").pprint(source)
        return uptodate

    def get_update_function(self, uptodate: Any) -> FnAction:
        """Create a ``doit.tools.config_changed``."""
        return cast(FnAction, doit.tools.config_changed(uptodate))
