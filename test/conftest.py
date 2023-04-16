"""Test configuration and fixtures for ``doitoml``."""
import logging
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, Generator, Tuple

import pytest
import tomli_w

try:
    __import__("jsone")
    HAS_JSONE = True
except (ImportError, AttributeError):
    HAS_JSONE = False

MSG_MISSING_JSONE = {"reason": "needs ``jsone`` installed"}

try:  # pragma: no cover
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib

if TYPE_CHECKING:  # pragma: no cover
    from doitoml import DoiTOML

TPyprojectMaker = Callable[[Any], Path]
TDataExample = Tuple[Path, Dict[str, Any]]

HERE = Path(__file__).parent
ROOT = HERE.parent

SELF_DODO = ROOT / "dodo.py"
SELF_PPT = ROOT / "pyproject.toml"

EXAMPLES_ROOT = ROOT / "examples"
EXAMPLE_PPT = sorted(EXAMPLES_ROOT.glob("*/pyproject.toml"))


@pytest.fixture(params=[p.parent.name for p in EXAMPLE_PPT])
def a_data_example(
    request: Any,
    tmp_path: Path,
) -> Generator[TDataExample, None, None]:
    """Generate an example with data-driven test information."""
    ppt = EXAMPLES_ROOT / f"{request.param}/pyproject.toml"
    example = ppt.parent
    ppt_data = tomllib.loads(ppt.read_text(encoding="utf-8"))
    ignores = (example / ".gitignore").read_text(encoding="utf-8").strip().splitlines()
    dest = tmp_path / f"{request.param}"
    shutil.copytree(example, dest, ignore=shutil.ignore_patterns(*ignores))
    old_cwd = Path.cwd()
    os.chdir(str(dest))
    yield dest, ppt_data["tool"].get("__doitoml_tests__", {})
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
