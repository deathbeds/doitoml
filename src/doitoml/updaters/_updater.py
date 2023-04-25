"""Uptodate checker base for ``doitoml``."""

import abc
from typing import TYPE_CHECKING, Any, Optional

from doitoml.types import FnAction

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
    def get_update_function(self, uptodate: Any) -> FnAction:
        """Get the run-time update checker."""

    def resolve_one_arg(self, source: "ConfigSource", arg_value: Any) -> Optional[Any]:
        """Resolve a single argument."""
        if isinstance(arg_value, str):
            found_kwarg = self.doitoml.config.resolve_one_path_spec(
                source,
                arg_value,
                source_relative=False,
            )
            return found_kwarg
        if isinstance(arg_value, list):
            found_kwarg = self.doitoml.config.resolve_some_path_specs(
                source,
                arg_value,
                source_relative=False,
            )[0]
            return found_kwarg
        return None
