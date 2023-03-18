"""Tests of bad parser data."""
from pathlib import Path

import pytest
from doitoml.errors import ParseError
from doitoml.sources.json.package import PackageJson


@pytest.mark.parametrize(
    "bad_package_json",
    [
        "[]",
        """{"doitoml": []}""",
    ],
)
def test_throws_parse_error(tmp_path: Path, bad_package_json: str) -> None:
    """Test for common parsing errors."""
    pj = tmp_path / "package.json"
    pj.write_text(bad_package_json, encoding="utf-8")
    p = PackageJson(pj)
    with pytest.raises(ParseError):
        assert p.raw_config
