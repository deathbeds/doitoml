"""Handles path/task discovery in ``package.json``."""
import re
from pathlib import Path
from typing import Any, Dict

from doitoml.constants import NAME
from doitoml.errors import ParseError
from doitoml.sources._config import ConfigParser, ConfigSource

from ._json import JsonSource


class PackageJson(JsonSource, ConfigSource):

    """An npm-compatible ``package.json``."""

    @property
    def raw_config(self) -> Dict[str, Any]:
        """Load ``doitoml`` configuration from ``pyproject.toml``."""
        tool_data = self.to_dict().get(NAME, {})
        if isinstance(tool_data, dict):
            return tool_data
        message = f"Expected a dictionary in {self.path}, found: {tool_data}"
        raise ParseError(message)


class PackageJsonParser(ConfigParser):

    """Entry point for parsing configuration from ``pyproject.toml``."""

    pattern = re.compile(r"package.json$")
    well_known = ("./package.json",)

    def __call__(self, path: Path) -> PackageJson:
        """Parse a ``doitoml`` configuration from ``pyproject.toml``."""
        return PackageJson(path)
