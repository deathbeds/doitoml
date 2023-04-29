"""Handles path/task discovery in ``pyproject.toml``."""
import re
from pathlib import Path
from typing import Any, Dict, cast

from doitoml.constants import NAME
from doitoml.sources._config import ConfigParser, ConfigSource

from ._toml import TomlSource

#: the "Wild West" top-level key
TOOL = "tool"


class PyprojectToml(TomlSource, ConfigSource):

    """Finds tasks and paths in ``pyproject.toml``."""

    @property
    def raw_config(self) -> Dict[str, Any]:
        """Load ``doitoml`` configuration from ``pyproject.toml``."""
        return cast(Dict[str, Any], self.to_dict().get(TOOL, {}).get(NAME, {}))


class PyprojectTomlParser(ConfigParser):

    """Entry point for parsing configuration from ``pyproject.toml``."""

    pattern = re.compile(r"pyproject.toml$")
    well_known = ("./pyproject.toml",)

    def __call__(self, path: Path) -> PyprojectToml:
        """Parse a ``doitoml`` configuration from ``pyproject.toml``."""
        return PyprojectToml(path)
