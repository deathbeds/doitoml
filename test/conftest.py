"""Test configuration and fixtures for ``doitoml``."""
import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator

import pytest
import tomli_w

if TYPE_CHECKING:  # pragma: no cover
    from doitoml import DoiTOML

TPyprojectMaker = Callable[[Any], Path]

HERE = Path(__file__).parent
ROOT = HERE.parent

SELF_DODO = ROOT / "dodo.py"
SELF_PPT = ROOT / "pyproject.toml"

EXAMPLES = ROOT / "examples"
WEB_EXAMPLE = EXAMPLES / "py-js-web"
NO_DODO_EXAMPLE = EXAMPLES / "no-dodo"
NO_DODO_JS_EXAMPLE = EXAMPLES / "no-dodo-js"
EXAMPLES = [WEB_EXAMPLE, NO_DODO_EXAMPLE, NO_DODO_JS_EXAMPLE]
EXAMPLE_INPUT_FILE_COUNTS = {
    # just ``pyproject.toml`` and ``.gitignore```
    NO_DODO_EXAMPLE.name: 2,
    # also a package.json
    NO_DODO_JS_EXAMPLE.name: 3,
    # a whole mess of stuff
    WEB_EXAMPLE.name: 16,
}
EXAMPLE_TASK_COUNTS = {
    NO_DODO_EXAMPLE.name: 2,
    NO_DODO_JS_EXAMPLE.name: 2,
    WEB_EXAMPLE.name: 10,
}
EXAMPLE_DEFAULT_OUTPUTS = {
    WEB_EXAMPLE.name: {
        "dist/*.whl": 1,
        "dist/*.tar.gz": 1,
        "dist/*.tgz": 1,
        "dist/SHA256SUMS": 1,
    },
    NO_DODO_EXAMPLE.name: {"*": 5, "*doit*": 3},
    NO_DODO_JS_EXAMPLE.name: {"*": 6, "*doit*": 3},
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


@pytest.fixture()
def empty_doitoml(tmp_path: Path) -> Generator["DoiTOML", None, None]:
    """Provide an empty doitoml."""
    from doitoml import DoiTOML

    old_cwd = Path.cwd()

    os.chdir(str(tmp_path))

    ppt = tmp_path / "pyproject.toml"

    ppt.write_text(
        """
        [tool.doitoml]
        log_level = "DEBUG"
        update_env = false
        """,
    )

    (tmp_path / "foo.txt").touch()
    (tmp_path / "bar.txt").touch()
    (tmp_path / "baz.json").write_text("""{"foo": ["bar", {"1": 2}, [false, null]]}""")

    doitoml = DoiTOML([ppt], log_level=logging.DEBUG, discover_config_paths=False)

    yield doitoml

    os.chdir(old_cwd)


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
