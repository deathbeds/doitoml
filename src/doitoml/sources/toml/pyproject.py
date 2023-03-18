"""Handles path/task discovery in ``pyproject.toml``."""
import re
from pathlib import Path
from typing import Any, Dict

from doitoml.constants import NAME
from doitoml.errors import ParseError
from doitoml.sources._config import ConfigParser, ConfigSource

from ._toml import TomlSource

#: the "Wild West" top-level key
TOOL = "tool"


class PyprojectToml(TomlSource, ConfigSource):

    """Finds tasks and paths in ``pyproject.toml``."""

    @property
    def raw_config(self) -> Dict[str, Any]:
        """Load ``doitoml`` configuration from ``pyproject.toml``."""
        loaded = self.parse().get(TOOL, {}).get(NAME, {})
        if not isinstance(loaded, dict):  # pragma: no cover
            message = f"Expected a dictionary, found {type(loaded)}"
            raise ParseError(message)
        return loaded


class PyprojectTomlParser(ConfigParser):

    """Entry point for parsing configuration from ``pyproject.toml``."""

    pattern = re.compile(r"pyproject.toml$")

    def __call__(self, path: Path) -> PyprojectToml:
        """Parse a ``doitoml`` configuration from ``pyproject.toml``."""
        return PyprojectToml(path)
