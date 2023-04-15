"""Task templates for ``doitoml``."""

import abc
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Optional

from doitoml.errors import TemplaterError, UnresolvedError

if TYPE_CHECKING:  # pragma: no cover
    from .doitoml import DoiTOML
    from .sources._config import ConfigSource


class Templater:

    """A base class for task templates."""

    doitoml: "DoiTOML"

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Create a new templater and remember the parent."""
        self.doitoml = doitoml

    @abc.abstractmethod
    def transform_task(self, source: "ConfigSource", task: Any) -> Any:
        """Transform a template into tasks."""


class JsonE(Templater):

    """A template driven by JSON-e."""

    def transform_task(self, source: "ConfigSource", task: Any) -> Any:
        """Transform an entire task, with ``paths``, ``cmd`` and ``env`` in context."""
        import jsone

        new_task = deepcopy(task)

        # expand map inputs
        dollar_map = new_task.get("$map", None)
        if dollar_map is not None:
            new_task["$map"] = self.expand_map(source, dollar_map)
        context = deepcopy(self.doitoml.config.to_dict())
        return jsone.render(new_task, context)

    def expand_map(self, source: "ConfigSource", dollar_map: Any) -> Any:
        """Pre-expand JSON-e ``$map`` operators, which cannot be dynamic."""
        new_map: Optional[Any] = None
        unresolved = None
        if isinstance(dollar_map, str):
            dollar_map = [dollar_map]

        if isinstance(dollar_map, dict):
            new_map = {}
            for k, v in dollar_map.items():
                new_submap, unresolved = self.doitoml.config.resolve_some_path_specs(
                    source,
                    v,
                    source_relative=False,
                )
                if unresolved:
                    break
                new_map[k] = str(new_submap)

        elif isinstance(dollar_map, list):
            new_map, unresolved = self.doitoml.config.resolve_some_path_specs(
                source,
                dollar_map,
                source_relative=False,
            )
            if new_map:
                new_map = list(map(str, new_map))

        if unresolved:
            message = f"$map had unresolved paths: {unresolved}"
            raise UnresolvedError(message)

        if not new_map:
            message = f"$map did not find anything: {dollar_map}"
            raise TemplaterError(message)

        return new_map
