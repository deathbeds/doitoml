"""A JSON Schema dumper for doitoml."""

import json
import sys
import warnings
from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from doitoml.constants import UTF8

PARSER = ArgumentParser()
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

GEN = Path(__file__).parent / "gen"

TYPE_SCHEMA_PATH = {
    "pyproject.toml": GEN / "_pyproject.v0.schema.json",
    "package.json": GEN / "_jspackage.v0.schema.json",
    "root": GEN / "_root.v0.schema.json",
}


@dataclass
class DumpArgs:

    """A typed container for schema dumping CLI options."""

    output: Optional[Path]
    type_: Literal["package.json", "pyproject.toml"]
    format_: Literal["json", "toml", "yaml"]


def main(args: DumpArgs) -> int:
    """Generate the dumped schema."""
    schema_path = TYPE_SCHEMA_PATH.get(str(args.type_) or "root")

    if schema_path is None:
        msg = f"Can't handle {args.type_}"
        warnings.warn(msg, stacklevel=2)
        return 1

    schema_text = schema_path.read_text(encoding=UTF8)
    schema = json.loads(schema_text)

    if args.format_ == "json":
        schema_text = json.dumps(schema, indent=2, sort_keys=True)
    elif args.format_ == "toml":
        import tomli_w

        schema_text = tomli_w.dumps(schema)
    elif args.format_ == "yaml":
        import yaml

        schema_text = yaml.safe_dump(schema)

    if args.output is None:
        sys.stdout.write(schema_text)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(schema_text, encoding=UTF8)

    return 0


if __name__ == "__main__":
    sys.exit(main(DumpArgs(**vars(PARSER.parse_args()))))
