"""Loads entry points."""
import sys
from typing import TYPE_CHECKING, Any, Dict, Tuple, Union

from .constants import (
    ENTRY_POINT_ACTOR,
    ENTRY_POINT_CONFIG,
    ENTRY_POINT_DSL,
    ENTRY_POINT_PARSER,
)
from .errors import EntryPointError

if sys.version_info < (3, 10):  # pragma: no cover
    from importlib_metadata import entry_points
else:  # pragma: no cover
    from importlib.metadata import entry_points

if TYPE_CHECKING:  # pragma: no cover
    from .actors import Actor
    from .doitoml import DoiTOML
    from .dsl import DSL
    from .sources._config import ConfigParser
    from .sources._source import Parser


class EntryPoints:

    """A collection of named ``entry_points``."""

    doitoml: "DoiTOML"
    dsl: Dict[str, "DSL"]
    parsers: Dict[str, "Parser"]
    config_parsers: Dict[str, "ConfigParser"]
    actors: Dict[str, "Actor"]

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Create a new collection of loaded ``entry_points``."""
        self.doitoml = doitoml

    def initialize(self) -> None:
        """Load all ``entry_points``."""
        # load the parsers
        self.config_parsers = self.load_entry_point_group(ENTRY_POINT_CONFIG)
        self.parsers = self.load_entry_point_group(ENTRY_POINT_PARSER)
        # load DSL, which might reference parsers
        self.dsl = self.load_entry_point_group(ENTRY_POINT_DSL)
        self.actors = self.load_entry_point_group(ENTRY_POINT_ACTOR)

    def load_entry_point_group(self, group: str) -> Dict[str, Any]:
        """Find and load ``entry_points`` from installed packages."""
        eps = {}

        for entry_point in entry_points(group=group):
            try:
                eps[entry_point.name] = entry_point.load()(self.doitoml)
            except Exception as err:  # pragma: no cover
                message = f"{group} {entry_point.name} failed to load: {err}"
                raise EntryPointError(message) from err

        return dict(sorted(eps.items(), key=self.rank_key))

    def rank_key(self, key_ep: Tuple[str, Any]) -> Tuple[Union[int, float], str]:
        """Return a sort key based on the ``entry_point``'s ``rank`` and key."""
        key, ep = key_ep
        return (getattr(ep, "rank", 100), key.lower())
