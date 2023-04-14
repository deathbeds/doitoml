"""Task templates for ``doitoml``."""

import abc
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

from doitoml.errors import TemplaterError, UnresolvedError

if TYPE_CHECKING:
    from .doitoml import DoiTOML
    from .sources._config import ConfigSource


def split_any(
    context: Dict[str, Any],  # noqa: ARG001
    any_token: Any,
    delimiter: str,
    maxsplit: Optional[int] = -1,
) -> List[str]:
    """Split just about anything after casting it to a string."""
    return f"{any_token}".split(delimiter, maxsplit=cast(int, maxsplit))


def rsplit_any(
    context: Dict[str, Any],  # noqa: ARG001
    any_token: Any,
    delimiter: str,
    maxsplit: Optional[int] = -1,
) -> List[str]:
    """Right split just about anything after casting it to a string."""
    return f"{any_token}".rsplit(delimiter, maxsplit=cast(int, maxsplit))


EXTRA_JSONE_BUILTINS = {"split_any": split_any, "rsplit_any": rsplit_any}

for fn in EXTRA_JSONE_BUILTINS.values():
    fn.__dict__["_jsone_builtin"] = True


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
        if isinstance(dollar_map, (str, dict)):
            message = f"Don't know what to do with $map {dollar_map}"
            raise TemplaterError(message)

        if isinstance(dollar_map, list):
            new_map, unresolved = self.doitoml.config.resolve_some_path_specs(
                source,
                dollar_map,
                source_relative=False,
            )
            if unresolved:
                message = f"$map had unresolved paths: {unresolved}"
                raise UnresolvedError(message)
            new_task["$map"] = new_map

        context = deepcopy(self.doitoml.config.to_dict())
        context.update(EXTRA_JSONE_BUILTINS)
        return jsone.render(new_task, context)
