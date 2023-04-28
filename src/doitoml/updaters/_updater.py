"""Uptodate checker base for ``doitoml``."""

import abc
from typing import TYPE_CHECKING, Any

from doitoml.types import ExecutionContext, FnAction

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
    def transform_uptodate(self, source: "ConfigSource", uptodate_args: Any) -> Any:
        """Replace uptodate tokens with DSL."""

    @abc.abstractmethod
    def get_update_function(
        self,
        uptodate: Any,
        execution_context: ExecutionContext,
    ) -> FnAction:
        """Get the run-time update checker."""
