"""Tests of this repo's data."""
from pathlib import Path
from typing import Any

import pytest

from .conftest import SELF_DODO, SELF_PPT

if not SELF_DODO.exists() and SELF_PPT.exists():
    pytest.skip("skipping self-tests", allow_module_level=True)


def test_self_parse(a_self_test_skeleton: Path, script_runner: Any) -> None:
    """A full end-to-end test of an example project."""
    assert (a_self_test_skeleton / "pyproject.toml").exists()
    r_list = script_runner.run("doit", "list")
    assert r_list.success
