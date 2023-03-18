"""Handles path/task discovery in ``package.json``."""
import re
from pathlib import Path
from typing import Any, Dict

from doitoml.constants import NAME
from doitoml.errors import ParseError
from doitoml.sources._config import ConfigParser, ConfigSource
from doitoml.sources._source import DictSource

from ._json import JsonSource


class PackageJson(JsonSource, DictSource, ConfigSource):

    """An npm-compatible ``package.json``."""

    @property
    def raw_config(self) -> Dict[str, Any]:
        """Load ``doitoml`` configuration from ``pyproject.toml``."""
        parsed = self.parse()

        if not isinstance(parsed, dict):  # pragma: no cover
            message = f"Expected a dictionary from {self.path}, found {type(parsed)}"
            raise ParseError(message)
        config = parsed.get(NAME, {})
        if not isinstance(config, dict):  # pragma: no cover
            message = f"Expected a dictionary from {self.path}, found {type(parsed)}"
            raise ParseError(message)
        return config


class PackageJsonParser(ConfigParser):

    """Entry point for parsing configuration from ``pyproject.toml``."""

    pattern = re.compile(r"package.json$")

    def __call__(self, path: Path) -> PackageJson:
        """Parse a ``doitoml`` configuration from ``pyproject.toml``."""
        return PackageJson(path)
