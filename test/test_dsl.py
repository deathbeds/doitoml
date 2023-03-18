"""Tests of ``doitoml`` DSL."""
import os
from pathlib import Path
from typing import Any, Generator, Type
from unittest import mock

import pytest
from doitoml.doitoml import DoiTOML
from doitoml.errors import EnvVarError


@pytest.fixture()
def empty_doitoml(tmp_path: Path) -> Generator[DoiTOML, None, None]:
    """Provide an empty doitoml."""
    old_cwd = Path.cwd()

    os.chdir(str(tmp_path))

    ppt = tmp_path / "pyproject.toml"

    ppt.write_text(
        """
    [doitoml]
    prefix = ""
    """,
    )

    doitoml = DoiTOML()

    yield doitoml

    os.chdir(old_cwd)


@pytest.mark.parametrize(
    ("key", "raw_token", "expected"),
    [("doitoml-dollar-env", "foo-${BAR}", EnvVarError)],
)
def test_dsl_fail(
    key: str,
    raw_token: str,
    expected: Type[Exception],
    empty_doitoml: DoiTOML,
) -> None:
    """Fail to parse some things."""
    source = empty_doitoml.config.sources[""]
    dsl = empty_doitoml.entry_points.dsl[key]
    match = dsl.pattern.search(raw_token)
    assert match is not None
    with pytest.raises(expected):
        dsl.transform_token(source, match, raw_token)


@pytest.mark.parametrize(
    ("key", "raw_token", "expected"),
    [("doitoml-dollar-env", "foo-${BAR}", ["foo-bar"])],
)
@mock.patch.dict(os.environ, {"BAR": "bar"})
def test_dsl_success(
    key: str,
    raw_token: str,
    expected: Any,
    empty_doitoml: DoiTOML,
) -> None:
    """Parse some happy days."""
    source = empty_doitoml.config.sources[""]
    dsl = empty_doitoml.entry_points.dsl[key]
    match = dsl.pattern.search(raw_token)
    assert match is not None
    observed = dsl.transform_token(source, match, raw_token)
    assert observed == expected
