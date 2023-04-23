"""Tests for ``doitoml`` schema."""
import pytest
from doitoml import DoiTOML
from doitoml.errors import SchemaError

from .conftest import TPyprojectMaker


def test_no_validate(a_pyproject_with: TPyprojectMaker) -> None:
    """Verify basic validation switches."""
    a_pyproject_with({"tasks": {}})
    doitoml = DoiTOML(validate=False)
    doitoml.config.tasks = {("0",): {"name": 1}}  # type: ignore
    with pytest.raises(SchemaError):
        doitoml.config.validate_all()
