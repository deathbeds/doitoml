"""JSON utilities for ``doitoml``."""
import json
import pathlib
from typing import Any

from doitoml.sources._source import Source


class DoitomlEncoder(json.JSONEncoder):

    """JSON Encoder aware of ``doitoml`` conventions.

    * always encode :class:`pathlib.Path` as a POSIX-style path (even on Windows).
    """

    def default(self, obj: Any) -> Any:
        """Handle a single object."""
        if isinstance(obj, pathlib.Path):
            return obj.as_posix()

        if isinstance(obj, Source):
            return obj.path.as_posix() if obj.path else None

        return json.JSONEncoder.default(self, obj)  # pragma: no cover


def to_json(obj: Any) -> Any:
    """Do an expensive roundtrip through JSON, just to be sure."""
    return json.loads(json.dumps(obj, cls=DoitomlEncoder, sort_keys=True))
