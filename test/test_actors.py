"""Tests for (bad) ``doitoml`` ``Actors``."""
from typing import Any, cast

import pytest
from doitoml import DoiTOML
from doitoml.errors import ActorError, NoActorError, TaskError
from doitoml.types import Task

from .conftest import TPyprojectMaker

DEFAULT_META = {"meta": {"doitoml": {"cwd": "."}}}


def test_no_actor(a_pyproject_with: TPyprojectMaker) -> None:
    """Test a missing actor."""
    a_pyproject_with({"tasks": {"foo": {"actions": [{"foo": "bar"}]}}})

    with pytest.raises(NoActorError):
        DoiTOML(fail_quietly=False)


@pytest.mark.parametrize(
    ("args", "kwargs", "message"),
    [
        (["::foo"], {}, "unresolved"),
        ([], {"bar": "::baz"}, "unresolved"),
        (0, {}, "unusable args"),
        ({"foo": 0}, {}, "unusable args"),
    ],
)
def test_bad_py_actor(
    a_pyproject_with: TPyprojectMaker,
    args: Any,
    kwargs: Any,
    message: str,
) -> None:
    """Test a badly-built actor."""
    a_pyproject_with(
        {
            "tasks": {
                "foo": {"actions": [{"py": "1:1", "args": args, "kwargs": kwargs}]},
            },
        },
    )

    with pytest.raises(ActorError, match=message):
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
