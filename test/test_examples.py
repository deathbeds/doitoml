"""Test example projects."""
import json
import os
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, Optional

try:  # pragma: no cover
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib


from .conftest import (
    TDataExample,
)


def _count_files(
    message: str,
    path: Path,
    expected_counts: Optional[Dict[str, str]],
) -> None:
    if not expected_counts:
        return
    observed = {}
    observed_counts = {}
    for globbish in expected_counts:
        paths = sorted(
            p.relative_to(path) for p in path.glob(globbish) if not p.is_dir()
        )
        observed[globbish] = paths
        observed_counts[globbish] = len(paths)
    pprint(observed)
    assert observed_counts == expected_counts, message


def _count_tasks(
    message: str,
    script_runner: Any,
    expected_count: Optional[int] = None,
    env: Optional[Dict[str, str]] = None,
) -> None:
    if expected_count is None:
        return

    list_all = script_runner.run(
        "doit",
        "list",
        "--all",
        "--template",
        "TASK: {name}",
        env=env or os.environ,
    )
    assert list_all.success
    stdout_lines = list_all.stdout.strip().splitlines()
    tasks = [t for t in stdout_lines if t.startswith("TASK:")]
    pprint(tasks)
    assert len(tasks) == expected_count, message


def test_example_file_count(a_data_example: TDataExample) -> None:
    """Test we're not pulling in dev files."""
    path, test_data = a_data_example
    name = path.name

    for step_name, step in sorted(test_data.get("steps", {}).items()):
        before = step.get("before", {})
        _count_files(f"{name} before {step_name}", path, before.get("files"))
        break


def test_example_config_ok(a_data_example: TDataExample) -> None:
    """Verify config files are well-formed."""
    path, test_data = a_data_example

    ppt = path / "pyproject.toml"
    if ppt.exists():
        assert tomllib.loads(ppt.read_text(encoding="utf-8"))
    pj = path / "package.json"
    if pj.exists():
        assert json.loads(pj.read_text(encoding="utf-8"))


def test_example_task_counts(a_data_example: TDataExample, script_runner: Any) -> None:
    """Test task counts are as expected."""
    path, test_data = a_data_example
    for _step_name, step in sorted(test_data.get("steps", {}).items()):
        _count_tasks(
            f"{path.name} tasks after list {_step_name}",
            script_runner,
            step["tasks"],
        )
        break


def test_slow_example(
    a_data_example: TDataExample,
    script_runner: Any,
) -> None:
    """Verify a data-driven example runs as expected."""
    path, test_data = a_data_example
    name = path.name

    if not test_data:
        print(f"TODO: add data-driven tests for {path.name}")
        return

    for step_name, step in sorted(test_data.get("steps", {}).items()):
        before = step.get("before", {})
        after = step.get("after", {})
        _count_files(f"{name} files before {step_name}", path, before.get("files"))
        env = dict(**os.environ)
        env.update(step.get("env", {}))
        res = script_runner.run(*step["run"], env=env)
        assert res.returncode == step["rc"]
        _count_files(f"{name} files after {step_name}", path, after.get("files"))
        _count_tasks(
            f"{name} tasks after {step_name}",
            script_runner,
            step.get("tasks"),
            env,
        )
