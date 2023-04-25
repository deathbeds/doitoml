"""Uptodate checker base for ``doitoml``."""

import abc
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from doitoml.doitoml import DoiTOML
    from doitoml.sources._config import ConfigSource


class Updater:

    """A base class for uptodate calcluators."""

    doitoml: "DoiTOML"

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Create a new updater and remember the parent."""
        self.doitoml = doitoml

    @abc.abstractmethod
    def transform_uptodate(self, source: "ConfigSource", uptodate: Any) -> Dict:
        """Replace uptodate tokens with DSL."""

    @abc.abstractmethod
    def is_uptodate(self, uptodate: Any) -> Optional[bool]:
        """Run-time update checker."""
