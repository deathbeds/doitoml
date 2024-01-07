"""Tests for schema dumping."""

import argparse
from pathlib import Path
from typing import TYPE_CHECKING, Generic, List, TypeVar

import pytest
from doitoml.schema import dump

if TYPE_CHECKING:
    from doitoml.schema.dump import TSchemaFormat, TSchemaType

    T = TypeVar("T")

    class FixtureRequest(pytest.FixtureRequest, Generic[T]):

        """A type-only generic fixture."""

        param: T
else:
    FixtureRequest = pytest.FixtureRequest


@pytest.fixture(params=["package.json", "pyproject.toml"])
def a_schema_type(request: "FixtureRequest[TSchemaType]") -> "TSchemaType":
    """Provide a schema container type."""
    return request.param


@pytest.fixture(params=["json", "yaml", "toml"])
def a_schema_format(request: "FixtureRequest[TSchemaFormat]") -> "TSchemaFormat":
    """Provide a serialization format."""
    return request.param


def _run_main(*args: str) -> None:
    """Run main, maybe fail."""
    dump_args = dump.DumpArgs(**vars(dump.PARSER.parse_args(args)))

    assert dump.main(dump_args) == 0


@pytest.mark.parametrize("output", [True, False])
def test_schema_dump_format_type(
    a_schema_format: "TSchemaFormat",
    a_schema_type: "TSchemaType",
    output: bool,
    tmp_path: Path,
) -> None:
    """Verify the CLI pretty much works."""
    args = ["--type", a_schema_type, "--format", a_schema_format]
    output_file = None
    if output:
        output_file = tmp_path / f"{a_schema_type}.schema.{a_schema_format}"
        args += ["--output", str(output_file)]
    _run_main(*args)
    if output_file is not None:
        assert output_file.exists()


@pytest.mark.parametrize(
    ("error_msg", "args"),
    [
        ("yaml", ["--format=dhall"]),
        ("package.json", ["--type=cargo.toml"]),
    ],
)
def test_schema_dump_args_fail(error_msg: str, args: List[str]) -> None:
    """Verify the CLI catches some bad behavior."""
    dump.PARSER.exit_on_error = False  # type: ignore
    with pytest.raises(argparse.ArgumentError, match=error_msg):
        _run_main(*args)


def test_schema_dump_type_fail() -> None:
    """Verify a bad container is caught."""
    with pytest.raises(ValueError, match="Can't handle"):
        dump.get_schema_dict("bower.json")  # type: ignore


def test_schema_dump_format_fail() -> None:
    """Verify a bad format is caught."""
    with pytest.raises(ValueError, match="Unrecognized"):
        dump.get_formatted_schema({}, "json5")  # type: ignore
