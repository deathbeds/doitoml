"""Tests of ``doitoml`` templaters."""

from typing import Any

import pytest
from doitoml import DoiTOML
from doitoml.errors import JsonEError, TemplaterError

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
    ("tasks", "message"),
    [
        ({"foo": {}}, "unexpectedly empty"),
    ],
)
def test_bad_templater_jsone_taks(
    a_pyproject_with: TPyprojectMaker,
    tasks: Any,
    message: str,
) -> None:
    """Test a badly-built template."""
    a_pyproject_with({"templates": {"json-e": {"tasks": tasks}}})

    with pytest.raises(JsonEError, match=message):
        DoiTOML(fail_quietly=False)
