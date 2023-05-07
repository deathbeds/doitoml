"""Basic boolean logic for skippers."""
from typing import TYPE_CHECKING, Any

from doitoml.errors import SkipError
from doitoml.skippers._skipper import Skipper

if TYPE_CHECKING:
    from doitoml.sources._config import ConfigSource


class Any_(Skipper):  # noqa: N801

    """A skipper that skips if any given item is truthy."""

    def should_skip(self, source: "ConfigSource", skip: Any) -> bool:
        """Skip if given any truthy value."""
        if not isinstance(skip, (tuple, list)):
            message = f"{source} Cannot skip `any`: {skip}"
            raise SkipError(message)
        return any(self.doitoml.config.resolve_one_skip(source, s) for s in skip)


class All(Skipper):

    """A skipper that skips if all given items is truthy."""

    def should_skip(self, source: "ConfigSource", skip: Any) -> bool:
        """Skip if given all truthy values."""
        if not isinstance(skip, (tuple, list)):
            message = f"{source} Cannot skip `all`: {skip}"
            raise SkipError(message)
        return all(self.doitoml.config.resolve_one_skip(source, s) for s in skip)


class Not(Skipper):

    """A skipper that skips if all given items is falsey."""

    def should_skip(self, source: "ConfigSource", skip: Any) -> bool:
        """Skip if falsey."""
        return not self.doitoml.config.resolve_one_skip(source, skip)
