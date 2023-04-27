"""Tests for (bad) ``doitoml`` ``Actors``."""
from typing import Any, Type, cast

import pytest
from doitoml import DoiTOML
from doitoml.errors import (
    DoitomlError,
    NoActorError,
    PyError,
    TaskError,
    UnresolvedError,
)
from doitoml.types import Task

from .conftest import TPyprojectMaker

DEFAULT_META = {"meta": {"doitoml": {"cwd": "."}}}


def test_no_actor(a_pyproject_with: TPyprojectMaker) -> None:
    """Test a missing actor."""
    a_pyproject_with({"tasks": {"foo": {"actions": [{"foo": "bar"}]}}})

    with pytest.raises(NoActorError):
        DoiTOML(fail_quietly=False)


@pytest.mark.parametrize(
    ("args", "kwargs", "message", "error_klass"),
    [
        (["::foo"], {}, "unresolved", UnresolvedError),
        ([], {"bar": "::baz"}, "unresolved", UnresolvedError),
        (0, {}, "unusable positional", PyError),
        ({"foo": 0}, {}, "unusable positional", PyError),
        ([], False, "unusable named", PyError),
    ],
)
def test_bad_py_actor(
    a_pyproject_with: TPyprojectMaker,
    args: Any,
    kwargs: Any,
    message: str,
    error_klass: Type[DoitomlError],
) -> None:
    """Test a badly-built actor."""
    a_pyproject_with(
        {
            "tasks": {
                "foo": {"actions": [{"py": {"1:1": {"args": args, "kwargs": kwargs}}}]},
            },
        },
    )

    with pytest.raises(error_klass, match=message):
        DoiTOML(fail_quietly=False)


def test_bad_performance(a_pyproject_with: TPyprojectMaker) -> None:
    """Test a (difficult to reproduce) bad actor."""
    a_pyproject_with({"tasks": {}})

    doitoml = DoiTOML(fail_quietly=False)
    task = cast(Task, {**DEFAULT_META, "actions": [{"nope": False}]})
    doitoml.config.tasks[("", "baz")] = task

    tasks = doitoml.tasks()

    with pytest.raises(TaskError, match="not a recognized action"):
        list(tasks["task_baz"]())
