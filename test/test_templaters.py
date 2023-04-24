"""Tests of ``doitoml`` templaters."""

from typing import Any, Type

import pytest
from doitoml import DoiTOML
from doitoml.errors import (
    DoitomlError,
    Jinja2Error,
    JsonEError,
    TemplaterError,
    UnresolvedError,
)

from .conftest import (
    HAS_JINJA2,
    HAS_JSONE,
    MSG_MISSING_JINJA2,
    MSG_MISSING_JSONE,
    TPyprojectMaker,
)


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
def test_bad_template_tasks(a_pyproject_with: TPyprojectMaker) -> None:
    """Test a badly-built template."""
    a_pyproject_with({"templates": {"json-e": {"tasks": []}}})

    with pytest.raises(TemplaterError):
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
    """Test a badly-built JSON-e template."""
    a_pyproject_with({"templates": {"json-e": {"tasks": tasks}}})

    with pytest.raises(error_type, match=message):
        DoiTOML(fail_quietly=False)


@pytest.mark.skipif(not HAS_JINJA2, **MSG_MISSING_JINJA2)
@pytest.mark.parametrize(
    ("error_type", "task", "message"),
    [
        (Jinja2Error, {"toml": "bar"}, "after a key"),
        (Jinja2Error, {"foo": "bar"}, "find parseable"),
    ],
)
def test_bad_templater_jinja_tasks(
    a_pyproject_with: TPyprojectMaker,
    error_type: Type[DoitomlError],
    task: Any,
    message: str,
) -> None:
    """Test a badly-built Jinja2 template."""
    a_pyproject_with({"templates": {"jinja2": {"tasks": {"foo": task}}}})

    with pytest.raises(error_type, match=message):
        DoiTOML(fail_quietly=False)
