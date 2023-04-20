"""Task template base for ``doitoml``."""

import abc
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from doitoml.doitoml import DoiTOML
    from doitoml.sources._config import ConfigSource


class Templater:

    """A base class for task templates."""

    doitoml: "DoiTOML"

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Create a new templater and remember the parent."""
        self.doitoml = doitoml

    @abc.abstractmethod
    def transform_task(self, source: "ConfigSource", task: Any) -> Any:
        """Transform a template into tasks."""
