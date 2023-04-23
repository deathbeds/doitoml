"""optional schema for ``doitoml``."""

from pathlib import Path
from pprint import pformat
from typing import Any, Mapping, Optional, cast

from doitoml.errors import MissingDependencyError, SchemaError
from doitoml.sources.toml._toml import tomllib

HAS_JSONSCHEMA = False

try:
    from jsonschema import Draft7Validator

    HAS_JSONSCHEMA = True
except ImportError as err:
    message = "install `doitoml[jsonschema]` or `jsonschema[format]`"
    raise MissingDependencyError(message) from err

HERE = Path(__file__).parent

AnyMapping = Mapping[str, Any]


__all__ = ["v1", "latest"]


class Version:

    """A schema for ``doitoml``."""

    path: Path
    #: the cached schema
    _schema: Optional[AnyMapping]
    #: the cached validator
    _validator: Optional[Draft7Validator]

    def __init__(self, version: str) -> None:
        """Initialize a validator."""
        self.path = HERE / f"v{version}.schema.toml"
        self._schema = None
        self._validator = None

    @property
    def schema(self) -> AnyMapping:
        """Get the cached schema."""
        if self._schema is None:  # pragma: no cover
            self._schema = cast(AnyMapping, tomllib.load(self.path.open("rb")))
        return self._schema

    @property
    def validator(self) -> Draft7Validator:
        """Get the cached validator."""
        if self._validator is None:  # pragma: no cover
            self._validator = Draft7Validator(schema=self.schema)
        return self._validator

    def validate(self, instance: Any) -> None:
        """Validate an instance."""
        errors = [*self.validator.iter_errors(instance)]

        if errors:
            message = f"Invalid doitoml data: {pformat(errors)}"
            raise SchemaError(message)


v1 = Version("1")

latest = v1
