"""Handles discovering, loading, and normalizing configuration."""
import abc
import re
from pathlib import Path
from typing import Any, Dict, Tuple

from doitoml.constants import DEFAULTS
from doitoml.types import Paths

from ._source import Parser, Source

#: the prefix key in ``doitoml`` configuration
PREFIX = "prefix"


class ConfigSource(Source):

    """A source of ``doitoml`` configuration."""

    @property
    def prefix(self) -> str:
        """Get the prefix for this configuration source."""
        return self.raw_config.get(PREFIX, "")

    @property
    def extra_config_paths(self) -> Paths:
        return [
            (self.path.parent / path).resolve()
            for path in self.raw_config.get(DEFAULTS.CONFIG_PATHS, [])
        ]

    @abc.abstractproperty
    def raw_config(self) -> Dict[str, Any]:
        """Extract a raw ``doitoml`` configuration from this source."""

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ConfigSource) and other.path == self.path

    def __repr__(self) -> str:
        """Format the source for warnings and errors."""
        return f"<{self.__class__.__name__} prefix='{self.prefix}' path='{self.path}'>"


class ConfigParser(Parser):
    @abc.abstractproperty
    def pattern(self) -> re.Pattern[str]:
        """Provide pattern of well-known file names this parser can load."""

    @abc.abstractproperty
    def well_known(self) -> Tuple[str, ...]:
        """Provide concrete, well-known relative file names this parser can load."""

    @abc.abstractmethod
    def __call__(self, path: Path) -> ConfigSource:  # pragma: no cover
        """Load a path as a config source."""
