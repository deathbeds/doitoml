"""TOML sources."""
from pathlib import Path
from typing import Any, Dict

from doitoml.errors import ParseError
from doitoml.sources._source import JsonLikeSource, Parser

try:  # pragma: no cover
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib


class TomlSource(JsonLikeSource):

    """A source of configuration in TOML."""

    def parse(self) -> Dict[str, Any]:
        """Parse the path with ``tomllib`` or equivalent."""
        parsed = tomllib.load(self.path.open("rb"))
        if not isinstance(parsed, dict):  # pragma: no cover
            message = f"Expected a dictionary from {self.path}, found {type(parsed)}"
            raise ParseError(message)
        return parsed


class TomlParser(Parser):

    """A parser for TOML files."""

    def __call__(self, path: Path) -> TomlSource:
        """Find a TOML Source."""
        return TomlSource(path)
