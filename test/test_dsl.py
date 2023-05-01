"""Tests of ``doitoml`` DSL."""
import os
from pathlib import Path
from typing import Any, Type
from unittest import mock

import pytest
from doitoml.doitoml import DoiTOML
from doitoml.errors import DslError, EnvVarError, ParseError

GET = "doitoml-colon-get"
GLOB = "doitoml-colon-glob"
ENV = "doitoml-dollar-env"


@pytest.mark.parametrize(
    ("key", "raw_token", "expected"),
    [
        (ENV, "foo-${BAR}", EnvVarError),
        (GET, ":get::json::baz.json::0", ParseError),
        (GET, ":get::json::nope.json::0", DslError),
        (GET, ":get::json::foo.txt::0", ParseError),
        (GET, ":get::json::baz.json::foo::2::1::0", ParseError),
    ],
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
    [
        (ENV, "foo-${BAR}", ["foo-bar"]),
        (GLOB, ":glob::.::*.txt::!bar.*", ["./foo.txt"]),
        (GET, ":get::json::baz.json::foo::0", ["bar"]),
        (GET, ":get::json::baz.json::foo::0::0", ["b"]),
        (GET, ":get::json::baz.json::foo", ["bar", '{"1": 2}', "[false, null]"]),
        (GET, ":get::json::baz.json::foo::1", ['{"1": 2}']),
        (GET, ":get::json::baz.json::foo::2", ["false", "null"]),
    ],
)
@mock.patch.dict(os.environ, {"BAR": "bar"})
def test_dsl_success(
    key: str,
    raw_token: str,
    expected: Any,
    empty_doitoml: DoiTOML,
    tmp_path: Path,
) -> None:
    """Parse some happy days."""
    source = empty_doitoml.config.sources[""]
    dsl = empty_doitoml.entry_points.dsl[key]
    match = dsl.pattern.search(raw_token)
    assert match is not None
    rel_expected = [
        (tmp_path / t).as_posix() if t.startswith("./") else t for t in expected
    ]
    observed = list(dsl.transform_token(source, match, raw_token))
    assert observed == rel_expected
