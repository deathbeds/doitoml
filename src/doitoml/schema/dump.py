"""A JSON Schema dumper for doitoml."""

import json
import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from doitoml.constants import UTF8

PARSER = ArgumentParser("doitoml-schema-dump")
PARSER.add_argument(
    "-t",
    "--type",
    type=str,
    default="pyproject.toml",
    choices=["pyproject.toml", "package.json"],
    help="target file container",
    dest="type_",
)
PARSER.add_argument(
    "-o", "--output", type=Path, default=None, help="the output file (or stdout)"
)
PARSER.add_argument(
    "-f",
    "--format",
    type=str,
    default="json",
    choices=["json", "yaml", "toml"],
    help="format to write",
    dest="format_",
)

GEN = Path(__file__).parent / "_gen"

TYPE_SCHEMA_PATH = {
    "pyproject.toml": GEN / "_pyproject.v0.schema.json",
    "package.json": GEN / "_jspackage.v0.schema.json",
    "root": GEN / "_root.v0.schema.json",
}

TSchemaType = Literal["package.json", "pyproject.toml"]
TSchemaFormat = Literal["json", "toml", "yaml"]


@dataclass
class DumpArgs:

    """A typed container for schema dumping CLI options."""

    output: Optional[Path]
    type_: TSchemaType
    format_: TSchemaFormat


def get_schema_dict(type_: TSchemaType) -> Dict[str, Any]:
    """Get a doitoml-aware schema as a dictionary."""
    schema_path = TYPE_SCHEMA_PATH.get(str(type_) or "root")

    if schema_path is None:
        msg = f"Can't handle {type_}"
        raise ValueError(msg)

    schema_text = schema_path.read_text(encoding=UTF8)
    return dict(json.loads(schema_text))


def get_formatted_schema(schema: Dict[str, Any], format_: TSchemaFormat) -> str:
    """Get a doitoml-aware schema as a formatted string."""
    if format_ == "json":
        schema_text = json.dumps(schema, indent=2, sort_keys=True)
    elif format_ == "toml":
        import tomli_w

        schema_text = tomli_w.dumps(schema)
    elif format_ == "yaml":
        import yaml

        schema_text = yaml.safe_dump(schema)
    else:
        msg = f"Unrecognized schema format {format_}"
        raise ValueError(msg)

    return schema_text


def write_schema(schema_text: str, output: Optional[Path] = None) -> None:
    """Write out a schema to a path or stdout."""
    if output is None:
        sys.stdout.write(schema_text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(schema_text, encoding=UTF8)


def main(args: DumpArgs) -> int:
    """Command-line entry to parse dumped schema."""
    schema = get_schema_dict(args.type_)
    schema_text = get_formatted_schema(schema, args.format_)
    write_schema(schema_text, args.output)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(DumpArgs(**vars(PARSER.parse_args()))))
