"""JSON-E templates for ``doitoml``."""

from copy import deepcopy
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from doitoml.errors import (
    JsonEError,
    MissingDependencyError,
    UnresolvedError,
)

try:
    import jsone
except ImportError as err:
    message = "install ``doitoml[jsone]`` or ``jsone`` to use JSON-e templates"
    raise MissingDependencyError(message) from err


from ._templater import Templater

if TYPE_CHECKING:
    from doitoml.sources._config import ConfigSource


class JsonE(Templater):

    """A templater driven by JSON-e."""

    def _expand_dict_map(
        self,
        source: "ConfigSource",
        dollar_map: Dict[Any, Any],
    ) -> Tuple[Dict[Any, Any], List[str]]:
        """Handle a dynamic dict ``$map``."""
        unresolved: List[str] = []
        new_map = {}
        for k, v in dollar_map.items():
            new_submap, k_unresolved = self.doitoml.config.resolve_some_path_specs(
                source,
                v,
                source_relative=False,
            )
            if new_submap:
                new_map[k] = new_submap[0]
            else:
                unresolved += [k]

        return new_map, unresolved

    def _expand_list_map(
        self,
        source: "ConfigSource",
        dollar_map: List[Any],
    ) -> Tuple[List[Any], List[str]]:
        """Pre-expand a dynamic JSON-e list ``$map``."""
        new_map, unresolved = self.doitoml.config.resolve_some_path_specs(
            source,
            dollar_map,
            source_relative=False,
        )
        return list(map(str, new_map)), unresolved

    def _expand_map(self, source: "ConfigSource", dollar_map: Any) -> Any:
        """Pre-expand JSON-e ``$map`` operators, not usually dynamic."""
        new_map: Optional[Any] = None
        unresolved = None

        if isinstance(dollar_map, str):
            dollar_map = [dollar_map]

        if isinstance(dollar_map, dict):
            new_map, unresolved = self._expand_dict_map(source, dollar_map)
        if isinstance(dollar_map, list):
            new_map, unresolved = self._expand_list_map(source, dollar_map)

        if unresolved:
            message = f"$map had unresolved paths: {unresolved}"
            raise UnresolvedError(message)

        if not new_map:
            message = f"$map did not find anything: {dollar_map}"
            raise JsonEError(message)

        return new_map

    def transform_task(self, source: "ConfigSource", task: Any) -> Any:
        """Transform a task template.

        ``paths``, ``tokens``, and ``env`` in context.
        """
        if not task:
            message = f"Task template was unexpectedly empty {task}"
            raise JsonEError(message)
        new_task = deepcopy(task)
        dollar_map = new_task.get("$map", None)
        if dollar_map is not None:
            new_task["$map"] = self._expand_map(source, dollar_map)
        context = self.doitoml.config.to_dict()
        return jsone.render(new_task, context)
