"""JSON utilities for ``doitoml``."""
import json
import pathlib
from typing import Any


class DoitomlEncoder(json.JSONEncoder):

    """JSON Encoder aware of ``doitoml`` conventions.

    * always encode :class:`pathlib.Path` as a POSIX-style path (even on Windows).
    """

    def default(self, obj: Any) -> Any:
        """Handle a single object."""
        if not isinstance(obj, pathlib.Path):  # pragma: no cover
            return json.JSONEncoder.default(self, obj)

        return obj.as_posix()


def to_json(obj: Any) -> Any:
    """Do an expensive roundtrip through JSON, just to be sure."""
    return json.loads(json.dumps(obj, cls=DoitomlEncoder, sort_keys=True))
