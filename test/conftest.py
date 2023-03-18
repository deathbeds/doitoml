"""Test configuration and fixtures for ``doitoml``."""
import os
import shutil
from pathlib import Path
from typing import Any, Generator

import pytest

HERE = Path(__file__).parent
ROOT = HERE.parent

SELF_DODO = ROOT / "dodo.py"
SELF_PPT = ROOT / "pyproject.toml"

EXAMPLES = ROOT / "examples"
WEB_EXAMPLE = EXAMPLES / "py-js-web"
EXAMPLES = [WEB_EXAMPLE]
EXAMPLE_INPUT_FILE_COUNTS = {
    WEB_EXAMPLE.name: 14,
}
EXAMPLE_DEFAULT_OUTPUTS = {
    WEB_EXAMPLE.name: {
        "dist/*.whl": 1,
        "dist/*.tar.gz": 1,
        "dist/*.tgz": 1,
    },
}

EXAMPLE_IGNORES = {
    example.name: (
        (example / ".gitignore").read_text(encoding="utf-8").strip().splitlines()
    )
    for example in EXAMPLES
}


@pytest.fixture(params=EXAMPLES)
def an_example_project(tmp_path: Path, request: Any) -> Generator[Path, None, None]:
    """Provide path to an example project."""
    dest = tmp_path / f"{request.param.name}"
    ignores = EXAMPLE_IGNORES[request.param.name]
    shutil.copytree(request.param, dest, ignore=shutil.ignore_patterns(*ignores))
    old_cwd = Path.cwd()
    os.chdir(str(dest))
    yield dest
    os.chdir(str(old_cwd))
    shutil.rmtree(dest)


@pytest.fixture()
def a_self_test_skeleton(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide ``doitoml``'s own ``doitoml`` configuration."""
    dest = tmp_path / "self"
    dest.mkdir(parents=True)
    for path in [SELF_DODO, SELF_PPT]:
        shutil.copy2(path, dest / path.name)
    old_cwd = Path.cwd()
    os.chdir(str(dest))
    yield dest
    os.chdir(str(old_cwd))
    shutil.rmtree(dest)
