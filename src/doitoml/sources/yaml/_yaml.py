"""YAML sources."""
from pathlib import Path
from typing import Any, Dict

from doitoml.errors import MissingDependencyError, ParseError
from doitoml.sources._source import JsonLikeSource, Parser

try:
    from yaml import safe_load
except ImportError as err:  # pragma: no cover
    message = "install ``doitoml[yaml]`` or ``pyyaml`` to use YAML sources"
    raise MissingDependencyError(message) from err


class YamlSource(JsonLikeSource):

    """A source of configuration in YAML."""

    def parse(self) -> Dict[str, Any]:
        """Parse the path with ``pyyaml``."""
        parsed = safe_load(self.path.open("rb"))
        if not isinstance(parsed, dict):  # pragma: no cover
            message = f"Expected a dictionary from {self.path}, found {type(parsed)}"
            raise ParseError(message)
        return parsed


class YamlParser(Parser):

    """A parser for YAML files."""

    def __call__(self, path: Path) -> YamlSource:
        """Find a YAML Source."""
        return YamlSource(path)
