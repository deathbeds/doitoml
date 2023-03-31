"""Test of (bad) ``doitoml`` configuration."""
import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Type

import pytest
import tomli_w
from doitoml.doitoml import DoiTOML
from doitoml.errors import (
    ConfigError,
    DoitomlError,
    PrefixError,
    UnresolvedError,
)

TPyprojectMaker = Callable[[Any], Path]


@pytest.fixture()
def a_pyproject_with(tmp_path: Path) -> Generator[TPyprojectMaker, None, None]:
    """Make a broken ``pyproject.toml``."""
    ppt = tmp_path / "pyproject.toml"

    def make_pyproject_toml(dotoml_cfg: Dict[str, Any]) -> Path:
        ppt_text = tomli_w.dumps({"tool": {"doitoml": dotoml_cfg}})
        ppt.write_text(ppt_text, encoding="utf-8")
        return ppt

    old_cwd = Path.cwd()
    os.chdir(str(tmp_path))
    yield make_pyproject_toml
    os.chdir(str(old_cwd))


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
