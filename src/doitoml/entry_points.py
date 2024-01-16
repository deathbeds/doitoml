"""Loads entry points."""
import sys
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Tuple, Union

from doitoml.errors import EntryPointError, MissingDependencyError

from .constants import ENTRY_POINTS

if sys.version_info < (3, 10):  # pragma: no cover
    from importlib_metadata import entry_points
else:  # pragma: no cover
    from importlib.metadata import entry_points

if TYPE_CHECKING:
    from .actors._actor import Actor
    from .doitoml import DoiTOML
    from .dsl import DSL
    from .skippers._skipper import Skipper
    from .sources._config import ConfigParser
    from .sources._source import Parser
    from .templaters._templater import Templater
    from .updaters._updater import Updater


class EntryPoints:

    """A collection of named ``entry_points``."""

    doitoml: "DoiTOML"
    dsl: Dict[str, "DSL"]
    parsers: Dict[str, "Parser"]
    config_parsers: Dict[str, "ConfigParser"]
    actors: Dict[str, "Actor"]
    templaters: Dict[str, "Templater"]
    updaters: Dict[str, "Updater"]
    skippers: Dict[str, "Skipper"]

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Create a new collection of loaded ``entry_points``."""
        self.doitoml = doitoml

    @staticmethod
    @lru_cache(1)
    def raw_entry_points(group: str) -> Dict[str, Any]:
        """Load and cache raw entry points."""
        raw_eps = {}
        for entry_point in entry_points(group=group):
            try:
                raw_eps[entry_point.name] = entry_point.load()
            except Exception as err:  # pragma: no cover
                message = (
                    f"{group} {entry_point.name} unexpectedly failed to load {err}"
                )
                raise EntryPointError(message) from err
        return dict(sorted(raw_eps.items()))

    def initialize(self) -> None:
        """Load all ``entry_points``."""
        # load the parsers
        self.config_parsers = self.load_entry_point_group(ENTRY_POINTS.CONFIG)
        self.parsers = self.load_entry_point_group(ENTRY_POINTS.PARSER)
        # load DSL, which might reference parsers
        self.dsl = self.load_entry_point_group(ENTRY_POINTS.DSL)
        self.actors = self.load_entry_point_group(ENTRY_POINTS.ACTOR)
        self.templaters = self.load_entry_point_group(ENTRY_POINTS.TEMPLATER)
        self.updaters = self.load_entry_point_group(ENTRY_POINTS.UPDATER)
        self.skippers = self.load_entry_point_group(ENTRY_POINTS.SKIPPER)

    def load_entry_point_group(self, group: str) -> Dict[str, Any]:
        """Find and load ``entry_points`` from installed packages."""
        eps = {}

        for name, entry_point in self.raw_entry_points(group).items():
            try:
                eps[name] = entry_point(self.doitoml)
            except MissingDependencyError as err:
                self.doitoml.log.info(
                    "%s %s is missing a dependency: %s",
                    group,
                    name,
                    err,
                )
            except Exception as err:  # pragma: no cover
                message = f"{group} {name} unexpectedly failed to load {err}"
                raise EntryPointError(message) from err

        return dict(sorted(eps.items(), key=self.rank_key))

    def rank_key(self, key_ep: Tuple[str, Any]) -> Tuple[Union[int, float], str]:
        """Return a sort key based on the ``entry_point``'s ``rank`` and key."""
        key, ep = key_ep
        return (getattr(ep, "rank", 100), key.lower())
