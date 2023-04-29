"""TOML sources."""
from pathlib import Path
from typing import Any

from doitoml.sources._source import JsonLikeSource, Parser

try:  # pragma: no cover
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib


class TomlSource(JsonLikeSource):

    """A source of configuration in TOML."""

    def parse(self, data: str) -> Any:
        """Parse the path with ``tomllib`` or equivalent."""
        return tomllib.loads(data)


class TomlParser(Parser):

    """A parser for TOML files."""

    def __call__(self, path: Path) -> TomlSource:
        """Find a TOML Source."""
        return TomlSource(path)
