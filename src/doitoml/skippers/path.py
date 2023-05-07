"""Path skippers."""
from pathlib import Path
from typing import TYPE_CHECKING, Any

from doitoml.errors import SkipError
from doitoml.skippers._skipper import Skipper

if TYPE_CHECKING:
    from doitoml.sources._config import ConfigSource


class Exists(Skipper):

    """A skipper that skips if all given paths exist."""

    def should_skip(self, source: "ConfigSource", skip: Any) -> bool:
        """Skip if (any) given path does not exist."""
        if not isinstance(skip, (str, tuple, list)):
            message = f"{source} Cannot skip `exists`: {skip}"
            raise SkipError(message)
        if isinstance(skip, str):
            skip = [skip]
        for one_skip in skip:
            spec_paths = self.doitoml.config.resolve_one_path_spec(
                source,
                one_skip,
                source_relative=True,
            )
            if not spec_paths:
                return False
            for spec in spec_paths:
                if not Path(spec).exists():
                    return False
        return True
