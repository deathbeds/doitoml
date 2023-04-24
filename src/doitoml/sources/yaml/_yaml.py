"""YAML sources."""
from pathlib import Path
from typing import Any

from doitoml.errors import MissingDependencyError
from doitoml.sources._source import JsonLikeSource, Parser

try:
    from yaml import safe_load
except ImportError as err:
    message = "install ``doitoml[yaml]`` or ``pyyaml`` to use YAML sources"
    raise MissingDependencyError(message) from err


class YamlSource(JsonLikeSource):

    """A source of configuration in YAML."""

    def parse(self, data: str) -> Any:
        """Parse the path with ``pyyaml``."""
        return safe_load(data)


class YamlParser(Parser):

    """A parser for YAML files."""

    def __call__(self, path: Path) -> YamlSource:
        """Find a YAML Source."""
        return YamlSource(path)
