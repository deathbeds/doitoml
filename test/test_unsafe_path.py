"""Test of unsafe paths in ``doitoml`` configuration."""
import json
from pathlib import Path
from pprint import pprint

import pytest
from doitoml.doitoml import DoiTOML
from doitoml.errors import UnsafePathError

from .conftest import TPyprojectMaker

UNSAFE_PATHS = {
    "dir": """{"paths": {"a": [DIR]}}""",
    "txt": """{"paths": {"a": [FILE]}}""",
    "log": """{"tasks": {"a": {ACT, "meta": {"doitoml": {"log": FILE}}}}}""",
    "cwd": """{"tasks": {"a": {ACT, "meta": {"doitoml": {"cwd": DIR}}}}}""",
}


@pytest.mark.parametrize("tmpl_key", sorted(UNSAFE_PATHS))
def test_safe_paths(
    tmpl_key: str,
    a_pyproject_with: TPyprojectMaker,
    tmp_path: Path,
) -> None:
    """Test that paths outside config parent paths are rejected."""
    print("CWD", Path.cwd())
    tmpl = UNSAFE_PATHS[tmpl_key]
    tdp = tmp_path.parent / "DANGER"
    tdp_p = tdp.as_posix()
    print(tdp_p)
    tdf_p = (tdp / "foo.txt").as_posix()
    tmpl = tmpl.replace("DIR", f""" "{tdp_p}" """)
    tmpl = tmpl.replace("FILE", f""" "{tdf_p}" """)
    tmpl = tmpl.replace("ACT", """ "actions": [["echo"]] """)
    loaded = json.loads(tmpl)
    pprint(loaded)
    a_pyproject_with(loaded)
    with pytest.raises(UnsafePathError, match="safe_paths"):
        pprint(DoiTOML(fail_quietly=False).config.tasks)
