"""JSON-E templates for ``doitoml``."""

from copy import deepcopy
from pprint import pformat
from typing import TYPE_CHECKING, Any, Optional

from doitoml.errors import (
    Jinja2Error,
    MissingDependencyError,
)

try:
    import jinja2
except ImportError as err:
    message = "install ``doitoml[jinja2]`` or ``jinja2`` to use Jinja2 templates"
    raise MissingDependencyError(message) from err


from ._templater import Templater

if TYPE_CHECKING:
    from doitoml.sources._config import ConfigSource
    from doitoml.sources._source import JsonLikeSource


class Jinja2(Templater):

    """A templater driven by Jinja2."""

    def transform_task(self, source: "ConfigSource", task: Any) -> Any:
        """Transform a task template.

        ``paths``, ``tokens``, and ``env`` in context.
        """
        message: Optional[str] = None
        context = deepcopy(self.doitoml.config.to_dict())

        for parser_name, parser in self.doitoml.entry_points.parsers.items():
            if parser_name in task:
                template = task[parser_name]
                rendered = jinja2.Template(template).render(**context)
                tmp_source: JsonLikeSource = parser(None)  # type: ignore
                try:
                    return tmp_source.parse(rendered)
                except Exception as err:  # noqa: BLE001
                    message = (
                        f"Failed to parse task in source {source}:"
                        "\n"
                        "task:\n"
                        f"{pformat(task)}"
                        "\n\n"
                        "template:\n"
                        f"{template}"
                        "\n\n"
                        "context:\n"
                        f"{pformat(context)}"
                        "\n\n"
                        "rendered:\n"
                        f"{rendered}"
                        "\n\n"
                        f"{type(err)}:"
                        "\n"
                        f"{err}"
                    )

        raise Jinja2Error(
            message or f"Failed to find parseable Jinja2 output in {source} {task}",
        )
