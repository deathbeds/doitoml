"""Test of (bad) ``doitoml`` configuration."""
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

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

FOO_PY = """
def foo():
    import os, sys
    print("FOO is {FOO}".format(**os.environ))
    print(os.environ["FOO"][::-1], file=sys.stderr)

if __name__ == "__main__":
    foo()
"""


@pytest.mark.parametrize(
    ("expected", "message", "items"),
    [
        (UnresolvedError, "resolve environment", {"env": {"a": "${b}"}}),
        (UnresolvedError, "resolve paths", {"paths": {"a": ["::b"]}}),
        (UnresolvedError, "resolve tokens", {"tokens": {"a": ["::b"]}}),
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


def test_task_env(a_pyproject_with: TPyprojectMaker, script_runner: Any) -> None:
    """Test task env customization and logs."""
    ppt = a_pyproject_with(
        {
            "doit": {"verbosity": 2, "loader": "doitoml"},
            "doitoml": {
                "env": {"FOO": "bar0"},
                "tokens": {"a": ["boo2"], "foo": ["python", "foo.py"]},
                "tasks": {
                    "foo": {
                        "meta": {"doitoml": {"env": {"FOO": "baz1"}}},
                        "actions": [["::foo"]],
                    },
                    "foo2": {
                        "meta": {"doitoml": {"log": "foo2.txt", "env": {"FOO": "::a"}}},
                        "actions": [["::foo"]],
                    },
                },
            },
        },
    )
    foo_py = ppt.parent / "foo.py"
    foo_py.write_text(FOO_PY)
    res = script_runner.run("doit", "foo")
    assert "FOO is baz" in res.stdout

    res = script_runner.run("doit", "foo2")
    foo2 = (ppt.parent / "foo2.txt").read_text(encoding="utf-8")
    assert "FOO is boo" in foo2
    assert "oob" in foo2


@pytest.mark.parametrize(
    "action",
    [["::foo"], {"py": {"foo:foo": {}}}],
)
@pytest.mark.parametrize(
    ("stdout", "stderr"),
    [
        ("out.txt", None),
        ("out.txt", ""),
        ("out.txt", "out.txt"),
        ("out.txt", "err.txt"),
        ("", "err.txt"),
    ],
)
def test_log(
    a_pyproject_with: TPyprojectMaker,
    script_runner: Any,
    stdout: str,
    stderr: Optional[str],
    action: Union[List[str], Dict[str, Any]],
) -> None:
    """Test task env customization and logs."""
    log = [stdout, stderr] if stderr is not None else stdout
    ppt = a_pyproject_with(
        {
            "doit": {"verbosity": 2, "loader": "doitoml"},
            "doitoml": {
                "env": {"FOO": "bar0"},
                "tokens": {"foo": ["python", "foo.py"]},
                "tasks": {
                    "foo": {
                        "meta": {"doitoml": {"log": log}},
                        "actions": [action],
                    },
                },
            },
        },
    )
    foo_py = ppt.parent / "foo.py"
    foo_py.write_text(FOO_PY)
    script_runner.run("doit")
    out = ppt.parent / "out.txt"
    err = ppt.parent / "err.txt"
    out_txt = None
    err_txt = None
    if stdout:
        out_txt = out.read_text(encoding="utf-8")
        assert "FOO is bar0" in out_txt
        if stderr in [None, stdout]:
            assert "rab" in out_txt
        elif not stderr:
            assert "rab" not in out_txt
    if stderr not in [stdout, None, ""]:
        err_txt = err.read_text()
        assert "rab" in err_txt
    script_runner.run("doit")


@pytest.mark.parametrize(
    ("err_klass", "stdout", "stderr"),
    [
        (ConfigError, "", ""),
        (ConfigError, ".", ""),
    ],
)
def test_bad_log(
    a_pyproject_with: TPyprojectMaker,
    err_klass: Type[DoitomlError],
    stdout: Any,
    stderr: Any,
) -> None:
    """Test some bad log paths."""
    ppt = a_pyproject_with(
        {
            "tasks": {
                "foo": {
                    "meta": {"doitoml": {"log": [stdout, stderr]}},
                    "actions": ["echo"],
                },
            },
        },
    )

    with pytest.raises(err_klass):
        DoiTOML([ppt], fail_quietly=False)


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


def test_config_path_get(a_pyproject_with: TPyprojectMaker) -> None:
    """Test custom paths for config paths."""
    ppt = a_pyproject_with(
        {
            "doitoml": {
                "config_paths": [":get::json::foo.json::"],
                "tasks": {"a": {"actions": ["echo"]}},
            },
        },
    )
    fj = ppt.parent / "foo.json"
    fj.write_text(
        json.dumps({"prefix": "foo", "tasks": {"a": {"actions": ["echo"]}}}),
        encoding="utf-8",
    )
    as_dict = DoiTOML(fail_quietly=False).config.to_dict()
    task_names = set(as_dict["tasks"])
    assert task_names == {":a", "foo:a"}
