"""optional schema for ``doitoml``."""

import os
from pathlib import Path
from pprint import pformat
from typing import Any, Mapping, Optional, cast

from doitoml.errors import MissingDependencyError, SchemaError
from doitoml.sources.toml._toml import tomllib

HAS_JSONSCHEMA = False

try:
    from jsonschema import Draft7Validator, ValidationError

    HAS_JSONSCHEMA = True
except ImportError as err:
    message = "install `doitoml[jsonschema]` or `jsonschema[format]`"
    raise MissingDependencyError(message) from err

HERE = Path(__file__).parent

AnyMapping = Mapping[str, Any]


__all__ = ["v0", "latest"]


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
        """Validate an instance.

        Something better would be https://json-schema.org/draft/2020-12/output/schema
        """
        errors = []
        error: ValidationError

        for error in self.validator.iter_errors(instance):
            schema_path = "/".join(list(map(str, error.relative_schema_path)))
            data_path = "/".join(list(map(str, error.relative_path)))
            errors += [
                {
                    "schema_path": f"#/{schema_path}",
                    "data_path": f"#/{data_path}",
                    "message": error.message,
                },
            ]

        if errors:
            message = f"Invalid doitoml data: {pformat(errors)}"
            raise SchemaError(message)


v0 = Version("0")

latest = v0

if os.environ.get("IN_SPHINX"):  # pragma: no cover
    DOITOML_SCHEMA = latest.schema
