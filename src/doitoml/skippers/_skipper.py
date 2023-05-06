"""Task skipper base for ``doitoml``."""

import abc
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from doitoml.doitoml import DoiTOML
    from doitoml.sources._config import ConfigSource


class Skipper:

    """A base class for task skippers."""

    doitoml: "DoiTOML"

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Create a new skipper and remember the parent."""
        self.doitoml = doitoml

    @abc.abstractmethod
    def should_skip(self, source: "ConfigSource", skip: Any) -> bool:
        """Evaluate whether a task should be skipped."""
