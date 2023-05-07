"""Tests of custom ``doitoml`` task skips."""

from pathlib import Path
from pprint import pprint
from typing import Any, Callable, Dict, Optional

import pytest
from doitoml.doitoml import DoiTOML
from doitoml.errors import SkipError

from .conftest import TPyprojectMaker


@pytest.mark.parametrize(
    ("task_count", "skip"),
    [
        (1, 0),
        (0, "1"),
        (1, {"all": [0, "TRUE"]}),
        (0, {"all": ["1", "99"]}),
        (1, {"any": [0, "FALSE"]}),
        (0, {"any": ["true", "TRUE"]}),
        (1, {"not": "true"}),
        (0, {"not": False}),
        (0, {"exists": ["pyproject.toml"]}),
        (1, {"exists": ["pyproject.toml", "nope"]}),
        (1, {"exists": ["::nope", "pyproject.toml"]}),
        (0, {"exists": "pyproject.toml"}),
        (1, {"platform": {"python_implementation": "Jython"}}),
        (0, {"py": {"platform:python_implementation": {}}}),
    ],
)
def test_good_skip(
    a_pyproject_with: TPyprojectMaker,
    skip: Any,
    task_count: int,
) -> None:
    """Verify expected skips work."""
    a_pyproject_with(
        {"tasks": {"a": {"meta": {"doitoml": {"skip": skip}}, "actions": [["echo"]]}}},
    )

    dt = DoiTOML(fail_quietly=False)
    pprint(dt.config.tasks)
    assert len(dt.config.tasks) == task_count


@pytest.mark.parametrize(
    ("match", "skip"),
    [
        (r"ambiguous: \[1\]", [1]),
        (r"Cannot skip `any`: 1", {"any": 1}),
        (r"not-a-skipper", {"not-a-skipper": 1}),
        (r"Cannot skip `all`: 1", {"all": 1}),
        (r"Cannot skip `exists`: 1", {"exists": 1}),
        (r"Cannot skip `platform`: 1", {"platform": 1}),
        (r"one `platform`: \{'a': 1, 'b': 2\}", {"platform": {"a": 1, "b": 2}}),
        (r"`platform.foo`", {"platform": {"foo": 1}}),
    ],
)
def test_bad_skip(
    a_pyproject_with: TPyprojectMaker,
    match: Optional[str],
    skip: Any,
) -> None:
    """Verify bad skips throw an expected error."""
    a_pyproject_with(
        {"tasks": {"a": {"meta": {"doitoml": {"skip": skip}}, "actions": [["echo"]]}}},
    )

    with pytest.raises(SkipError, match=match):
        pprint(DoiTOML(fail_quietly=False).config.tasks)


def test_null_skip(a_package_json_with: Callable[[Dict[str, Any]], Path]) -> None:
    """Test null (can't be in TOML)."""
    a_package_json_with(
        {"tasks": {"a": {"actions": [["echo"]], "meta": {"doitoml": {"skip": None}}}}},
    )
    dt = DoiTOML()
    pprint(dt.config.tasks)
    assert len(dt.config.tasks) == 1
