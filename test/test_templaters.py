"""Tests of ``doitoml`` templaters."""

from typing import Any, Type

import pytest
from doitoml import DoiTOML
from doitoml.errors import DoitomlError, JsonEError, TemplaterError, UnresolvedError

from .conftest import HAS_JSONE, MSG_MISSING_JSONE, TPyprojectMaker


@pytest.mark.parametrize(
    ("templates", "message"),
    [
        ({"not-a-templater": {"tasks": {}}}, "not-a-templater not one of"),
    ],
)
def test_bad_templater(
    a_pyproject_with: TPyprojectMaker,
    templates: Any,
    message: str,
) -> None:
    """Test a badly-built template."""
    a_pyproject_with({"templates": templates})

    with pytest.raises(TemplaterError, match=message):
        DoiTOML(fail_quietly=False)


@pytest.mark.skipif(not HAS_JSONE, **MSG_MISSING_JSONE)
@pytest.mark.parametrize(
    ("error_type", "tasks", "message"),
    [
        (JsonEError, {"foo": {}}, "unexpectedly empty"),
        (UnresolvedError, {"foo": {"$map": {"bar": ["::baz"]}}}, "unresolved"),
        (JsonEError, {"foo": {"$map": 0}}, "anything"),
    ],
)
def test_bad_templater_jsone_taks(
    a_pyproject_with: TPyprojectMaker,
    error_type: Type[DoitomlError],
    tasks: Any,
    message: str,
) -> None:
    """Test a badly-built template."""
    a_pyproject_with({"templates": {"json-e": {"tasks": tasks}}})

    with pytest.raises(error_type, match=message):
        DoiTOML(fail_quietly=False)
