"""Handles discovering, loading, and normalizing configuration."""
import abc
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Generator, List, Optional, Tuple, cast

from doitoml.constants import DEFAULTS
from doitoml.errors import ConfigError
from doitoml.types import Strings

from ._source import Parser, Source

#: the prefix key in ``doitoml`` configuration
PREFIX = "prefix"

if TYPE_CHECKING:
    from doitoml import DoiTOML
    from doitoml.dsl import Getter


class ConfigSource(Source):

    """A source of ``doitoml`` configuration."""

    @property
    def prefix(self) -> str:
        """Get the prefix for this configuration source."""
        return self.raw_config.get(PREFIX, "")

    def extra_config_sources(
        self,
        doitoml: "DoiTOML",
    ) -> Generator["ConfigSource", None, None]:
        getter: Optional["Getter"] = cast(
            "Getter",
            doitoml.entry_points.dsl.get("doitoml-colon-get"),
        )

        if getter is None:  # pragma: no cover
            message = "Can't find getter DSL"
            raise ConfigError(message)

        for path_spec in self.raw_config.get(DEFAULTS.CONFIG_PATHS, []):
            match = getter.pattern.search(path_spec)
            if match:
                child_source, bits = getter.get_source_with_key(self, match, path_spec)
                yield WrapperConfigSource(child_source, bits)
            else:
                path = (self.path.parent / path_spec).resolve()
                yield doitoml.config.load_config_source(path)

    @abc.abstractproperty
    def raw_config(self) -> Dict[str, Any]:
        """Extract a raw ``doitoml`` configuration from this source."""

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, ConfigSource) and other.path == self.path

    def __repr__(self) -> str:
        """Format the source for warnings and errors."""
        return (
            f"<{self.__class__.__name__}"
            f" prefix='{self.prefix}' "
            f" path='{os.path.relpath(str(self.path), str(Path.cwd()))}'"
            f">"
        )


class WrapperConfigSource(ConfigSource):

    """A config source which wraps another source with a specific root."""

    child_source: Source
    bit_prefix: Strings
    _raw_config: Dict[str, Any]

    def __init__(self, child_source: Source, bit_prefix: Strings) -> None:
        """Initialize a source, remembering its child and ``get`` bits."""
        self.bit_prefix = bit_prefix
        self.child_source = child_source
        self.path = child_source.path

    def read(self) -> Any:  # pragma: no cover
        message = "A wrapper source cannot `read`."
        raise NotImplementedError(message)

    def parse(self, data: str) -> Any:  # noqa: ARG002
        message = "A wrapper source cannot `parse`."  # pragma: no cover
        raise NotImplementedError(message)  # pragma: no cover

    @property
    def raw_config(self) -> Dict[str, Any]:
        """Get the ``doitoml`` configuration from the prefixed child source."""
        parsed = self.child_source.get(self.bit_prefix)
        if not isinstance(parsed, dict):  # pragma: no cover
            message = (
                f"Expected dictionary from source {self.child_source}:{self.bit_prefix}"
            )
            raise ConfigError(message)
        return parsed

    def get(self, bits: List[Any]) -> Any:  # pragma: no cover
        """Get a specific ``doitoml`` configuration piece."""
        return self.child_source.get([*self.bit_prefix, *bits])


class ConfigParser(Parser):

    """A parser that knows how to find well-known sources."""

    @abc.abstractproperty
    def pattern(self) -> re.Pattern[str]:
        """Provide pattern of well-known file names this parser can load."""

    @abc.abstractproperty
    def well_known(self) -> Tuple[str, ...]:
        """Provide concrete, well-known relative file names this parser can load."""

    @abc.abstractmethod
    def __call__(self, path: Path) -> ConfigSource:  # pragma: no cover
        """Load a path as a config source."""
