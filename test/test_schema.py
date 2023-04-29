"""Tests for ``doitoml`` schema."""
import pytest
from doitoml import DoiTOML
from doitoml.errors import SchemaError

from .conftest import TPyprojectMaker

BAD_TASK = {
    "name": 1,
    "meta": {"doitoml": {"cwd": ".", "env": {}, "source": "foo", "log": ["", ""]}},
}


def test_no_validate(a_pyproject_with: TPyprojectMaker) -> None:
    """Verify basic validation switches."""
    a_pyproject_with({"tasks": {}})
    doitoml = DoiTOML(validate=False)
    doitoml.config.tasks = {("0",): BAD_TASK}  # type: ignore
    with pytest.raises(SchemaError):
        doitoml.config.validate_all()
