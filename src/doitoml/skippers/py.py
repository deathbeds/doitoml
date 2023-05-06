"""User-defined Python skippers."""
import json
import platform
import re
from typing import TYPE_CHECKING, Any

from doitoml.errors import SkipError
from doitoml.skippers._skipper import Skipper

if TYPE_CHECKING:
    from doitoml.sources._config import ConfigSource


class Platform(Skipper):

    """A skipper that skips if the given value from Python's ``platform`` matches."""

    def should_skip(self, source: "ConfigSource", skip: Any) -> bool:
        """Skip if (any) given path does not exist."""
        if not isinstance(skip, dict):
            message = f"{source} Cannot skip `platform`: {skip}"
            raise SkipError(message)

        if len(skip) > 1:
            message = f"{source} can only skip based on one `platform`: {skip}"
            raise SkipError(message)

        key, pattern = list(skip.items())[0]

        func = getattr(platform, key, None)

        if not callable(func):
            message = f"{source} cannot skip based on `platform.{key}`"
            raise SkipError(message)

        value = func()
        value = value if isinstance(value, str) else json.dumps(value)
        return re.match(pattern, value) is not None
