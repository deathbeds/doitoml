"""Test of (bad) ``doitoml`` configuration."""
import json
import shutil
from pathlib import Path
from typing import Any, Dict, Type

import pytest
from doitoml.doitoml import DoiTOML
from doitoml.errors import (
    ActionError,
    ConfigError,
    DoitomlError,
    NoConfigError,
    PrefixError,
    UnresolvedError,
)

from .conftest import TPyprojectMaker


@pytest.mark.parametrize(
    ("expected", "message", "items"),
    [
        (UnresolvedError, "resolve environment", {"env": {"a": "${b}"}}),
        (UnresolvedError, "resolve paths", {"paths": {"a": ["::b"]}}),
        (UnresolvedError, "resolve commands", {"cmd": {"a": ["::b"]}}),
        (ConfigError, "not a dict", {"tasks": {"a": []}}),
        (UnresolvedError, "paths", {"tasks": {"a": {"actions": [["::b"]]}}}),
        (
            UnresolvedError,
            "paths",
            {"tasks": {"a": {"actions": [["::b"]], "file_dep": ["::b"]}}},
        ),
    ],
)
def test_bad_doitoml(
    expected: Type[DoitomlError],
    message: str,
    items: Dict[str, Any],
    a_pyproject_with: TPyprojectMaker,
) -> None:
    """Verify errors are thrown when data is missing."""
    ppt = a_pyproject_with(items)
    print(ppt.read_text(encoding="utf-8"))
    with pytest.raises(expected, match=message):
        DoiTOML([ppt, ppt], update_env=False, fail_quietly=False)


def test_bad_prefixes(a_pyproject_with: TPyprojectMaker, tmp_path: Path) -> None:
    """Verify prefix collision is caught."""
    ppt = a_pyproject_with(
        {"prefix": "a", "config_paths": ["package.json"]},
    )
    another_ppt = ppt.parent / "foo/pyproject.toml"
    another_ppt.parent.mkdir()
    shutil.copy2(ppt, another_ppt)
    pj = tmp_path / "package.json"
    pj.write_text(
        json.dumps(
            {
                "doitoml": {
                    "prefix": "a",
                    "config_paths": [
                        "foo/pyproject.toml",
                        "pyproject.toml",
                        "pyproject.toml",
                    ],
                },
            },
        ),
        encoding="utf-8",
    )
    with pytest.raises(PrefixError):
        DoiTOML([pj], update_env=False)


def test_unknown_config(a_pyproject_with: TPyprojectMaker, tmp_path: Path) -> None:
    """Verify unknown configs are caught."""
    a_pyproject_with({})
    foo = tmp_path / "foo.txt"
    with pytest.raises(ConfigError, match="expected one of"):
        DoiTOML([foo], update_env=False)


def test_env_collision(a_pyproject_with: TPyprojectMaker, tmp_path: Path) -> None:
    """Verify environment variables collisions behave as expected."""
    ppt = a_pyproject_with({"env": {"foo": "1"}})
    pj = tmp_path / "package.json"
    pj.write_text(
        json.dumps({"doitoml": {"prefix": "b", "env": {"foo": "2"}}}),
        encoding="utf-8",
    )

    doitoml = DoiTOML([ppt, pj], update_env=False)
    assert doitoml.get_env("foo") == "1"

    doitoml = DoiTOML([pj, ppt], update_env=False)
    assert doitoml.get_env("foo") == "2"


def test_fail_quietly(a_pyproject_with: TPyprojectMaker) -> None:
    """Test short fails."""
    ppt = a_pyproject_with({"env": {"foo": "${bar}"}})

    with pytest.raises(SystemExit):
        DoiTOML([ppt], fail_quietly=True)


def test_no_config(a_pyproject_with: TPyprojectMaker) -> None:
    """Test quick fail when no config is found."""
    ppt = a_pyproject_with({})
    ppt.unlink()

    with pytest.raises(NoConfigError):
        DoiTOML(discover_config_paths=False)


def test_fallback_config(a_pyproject_with: TPyprojectMaker) -> None:
    """Test... something with an empty config."""
    a_pyproject_with({"prefix": ""})

    DoiTOML(discover_config_paths=False)


def test_bad_action(a_pyproject_with: TPyprojectMaker) -> None:
    """Test a bad action."""
    a_pyproject_with({"tasks": {"a": {"actions": [0]}}})

    with pytest.raises(ActionError):
        DoiTOML(fail_quietly=False)
