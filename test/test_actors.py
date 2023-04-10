"""Tests for (bad) ``doitoml`` ``Actors``."""
from typing import Any

import pytest
from doitoml import DoiTOML
from doitoml.errors import ActorError, NoActorError, TaskError

from .conftest import TPyprojectMaker


def test_no_actor(
    a_pyproject_with: TPyprojectMaker,
) -> None:
    """Test a missing actor."""
    a_pyproject_with({"tasks": {"foo": {"actions": [{"foo": "bar"}]}}})

    with pytest.raises(NoActorError):
        DoiTOML(fail_quietly=False)


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["::foo"], "unresolved positional"),
        (0, "unusuable"),
        ({"foo": 0}, "unresolved named"),
    ],
)
def test_bad_py_actor(
    a_pyproject_with: TPyprojectMaker,
    args: Any,
    message: str,
) -> None:
    """Test a badly-built actor."""
    a_pyproject_with({"tasks": {"foo": {"actions": [{"py": "1", "args": args}]}}})

    with pytest.raises(ActorError, match=message):
        DoiTOML(fail_quietly=False)


def test_bad_performance(a_pyproject_with: TPyprojectMaker) -> None:
    """Test a (difficult to reproduce) bad actor."""
    a_pyproject_with({"tasks": {}})

    doitoml = DoiTOML(fail_quietly=False)
    doitoml.config.tasks[("", "baz")] = {"actions": [{"nope": False}]}  # type: ignore

    tasks = doitoml.tasks()

    with pytest.raises(TaskError, match="not a recognized action"):
        list(tasks["task_baz"]())
