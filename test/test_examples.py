"""Test example projects."""

import json
from pathlib import Path
from typing import Any

try:  # pragma: no cover
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib


from .conftest import EXAMPLE_DEFAULT_OUTPUTS, EXAMPLE_INPUT_FILE_COUNTS


def test_example_file_count(an_example_project: Path) -> None:
    """Test we're not pullin dev files."""
    expected_file_count = EXAMPLE_INPUT_FILE_COUNTS[an_example_project.name]
    all_files = sorted(p for p in an_example_project.rglob("*") if not p.is_dir())
    assert len(all_files) == expected_file_count


def test_example_doit_default(an_example_project: Path, script_runner: Any) -> None:
    """A full end-to-end test of an example project."""
    ppt = an_example_project / "pyproject.toml"
    if ppt.exists():
        assert tomllib.loads(ppt.read_text(encoding="utf-8"))
    pj = an_example_project / "package.json"
    if pj.exists():
        assert json.loads(pj.read_text(encoding="utf-8"))
    r_list = script_runner.run("doit", "list")
    assert r_list.success
    script_runner.run("doit")
    assert r_list.success
    observed = {}
    expected = {}
    for output_glob, count in EXAMPLE_DEFAULT_OUTPUTS[an_example_project.name].items():
        observed[output_glob] = len(sorted(an_example_project.glob(output_glob)))
        expected[output_glob] = count

    assert observed == expected
