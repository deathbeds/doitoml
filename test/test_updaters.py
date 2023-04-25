"""Tests of ``doitoml`` uptodate checkers."""

from typing import Any, List, Type

import pytest
from doitoml import DoiTOML
from doitoml.errors import ConfigError, DoitomlError, SchemaError

from .conftest import TPyprojectMaker


@pytest.mark.parametrize(
    ("config_changed"),
    [
        "a",
        ["a"],
        {"b": 1},
    ],
)
def test_config_changed(
    config_changed: Any,
    a_pyproject_with: TPyprojectMaker,
) -> None:
    """Test some config_changed."""
    a_pyproject_with(
        {
            "tasks": {
                "foo": {
                    "uptodate": [{"config_changed": config_changed}],
                    "actions": [["echo", "hello"]],
                },
            },
        },
    )
    dt = DoiTOML()
    tasks = dt.tasks()
    dt.config.to_dict()
    assert tasks
    # TODO: verify behavior


@pytest.mark.parametrize(
    ("error_klass", "message", "uptodate"),
    [
        (SchemaError, "Invalid", {}),
        (ConfigError, "unresolved", [{"foo": "bar"}]),
        (ConfigError, "unresolved", [{"foo": "::bar"}]),
    ],
)
def test_bad_updater(
    uptodate: Any,
    a_pyproject_with: TPyprojectMaker,
    error_klass: Type[DoitomlError],
    message: str,
) -> None:
    """Test bad config is caught."""
    a_pyproject_with(
        {
            "tasks": {
                "foo": {
                    "uptodate": uptodate,
                    "actions": [["echo", "hello"]],
                },
            },
        },
    )
    with pytest.raises(error_klass, match=message):
        DoiTOML(fail_quietly=False)


@pytest.mark.parametrize(
    "uptodate",
    [[True], ["yep"]],
)
def test_plain_uptodate(uptodate: List[Any], a_pyproject_with: TPyprojectMaker) -> None:
    """Test passthrough values."""
    a_pyproject_with(
        {
            "tasks": {
                "foo": {
                    "uptodate": uptodate,
                    "actions": [["echo", "hello"]],
                },
            },
        },
    )
    dt = DoiTOML()
    dt.tasks()
    task = list(dt.config.to_dict()["tasks"].values())[0]
    assert task["uptodate"][0] == uptodate[0]
