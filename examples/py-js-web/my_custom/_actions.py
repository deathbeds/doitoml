"""Python actions for ``doitoml``."""
import json
import subprocess
from hashlib import sha256
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING, Any, Generator, List, Optional, Union

try:
    import tomllib
except ImportError:
    import tomli as tomllib

if TYPE_CHECKING:
    import referencing

UTF8 = {"encoding": "utf-8"}

PathOrString = Union[Path, str]
Rootish = Optional[Union[PathOrString, List[PathOrString]]]


def _hash_one(
    root: Path,
    pathish: PathOrString,
    hashfile: Path,
) -> Generator[str, None, None]:
    """Hash one file (or glob), relative to the root."""
    if isinstance(pathish, str) and "*" in pathish:
        for globbed in root.glob(pathish):
            yield from _hash_one(root, globbed, hashfile)
    else:
        path = Path(pathish)
        if path == hashfile:
            return
        rel_path = path.relative_to(root).as_posix()
        yield f"{sha256(Path(path).read_bytes()).hexdigest()}  {rel_path}"


def _clean_hashfile(hashfile: Union[PathOrString, List[PathOrString]]) -> Path:
    """Condition and clean out an existing hashfile."""
    if isinstance(hashfile, Path):
        return hashfile

    if isinstance(hashfile, str):
        return Path(hashfile)

    if len(hashfile) == 1:
        return Path(hashfile[0])

    message = f"hashfile must be exactly one file, got {hashfile}"
    raise ValueError(message)


def _clean_root(root: Rootish, hashfile: Path) -> Path:
    if root is None:
        return hashfile.parent
    if isinstance(root, Path):
        return root
    if isinstance(root, str):
        return Path(root).resolve()
    if isinstance(hashfile, list) and len(hashfile) == 1:
        return Path(root[0]).resolve()
    message = (
        f"root must be exactly one file, or None (parent of {hashfile}), got {root}"
    )
    raise ValueError(message)


def hash_files(
    hashfile: Union[PathOrString, List[PathOrString]],
    files: Union[PathOrString, List[PathOrString]],
    *extra_files: PathOrString,
    root: Rootish = None,
    quiet: Optional[bool] = False,
) -> None:
    """Emulate ``sha256sum`` to write out a file."""
    hashfile = _clean_hashfile(hashfile)
    root = _clean_root(root, hashfile)
    lines = []

    if hashfile.exists():
        hashfile.unlink()

    all_files = [*extra_files]

    if isinstance(files, (str, Path)):
        all_files += [files]
    elif isinstance(files, list):
        all_files += files
    else:
        message = f"Unexpected files {type(files)}: {files}"
        raise ValueError(message)

    for path in sorted(all_files):
        lines += list(_hash_one(root, path, hashfile))

    output = "\n".join(lines) + "\n"

    if not hashfile.parent.exists():
        hashfile.parent.mkdir(parents=True)

    hashfile.write_text(output, **UTF8)

    if not quiet:
        print(output)


def toml2json(src_path: str, dest_path: str) -> None:
    src = Path(src_path)
    dest = Path(dest_path)
    dest.parent.mkdir(exist_ok=True, parents=True)
    dest.write_text(
        json.dumps(tomllib.loads(src.read_text(**UTF8)), indent=2, sort_keys=True),
        **UTF8,
    )


def source_date_epoch() -> None:
    """Get the source date epoch by shelling out to ``git``."""
    sde = subprocess.check_output(["git", "log", "-1", "--pretty=%ct"])
    print(json.dumps({"SOURCE_DATE_EPOCH": sde.decode("utf-8").strip()}))


def replace_between(src: str, dest: str, sep: str) -> Optional[bool]:
    """Copy the text between a separator from a source to a destination path."""
    print("  ...", sep, "\n    +--", src, "\n    +->", dest)
    src_chunks = Path(src).read_text(**UTF8).split(sep)
    dest_chunks = Path(dest).read_text(**UTF8).split(sep)
    assert len(src_chunks) == 3, pformat(src_chunks)
    assert len(dest_chunks) == 3, pformat(dest_chunks)
    Path(dest).write_text(
        "".join([dest_chunks[0], sep, src_chunks[1], sep, dest_chunks[2]]),
        **UTF8,
    )
    return True


def load_one(path: str) -> Any:
    """Load a JSON-like data file."""
    path_text = Path(path).read_text(**UTF8)
    if path.endswith(".json"):
        return json.loads(path_text)
    if path.endswith(".toml"):
        return tomllib.loads(path_text)
    if path.endswith(".yaml"):
        import yaml

        return yaml.safe_load(path_text)
    msg = f"can't parse {path}"
    raise NotImplementedError(msg)


def _get_registry(schema_dir: Path) -> "referencing.Registry":
    from referencing import Registry, Resource

    resources = {}

    for schema_json in schema_dir.glob("*.schema.json"):
        schema = load_one(str(schema_json))
        resources[schema["$id"]] = Resource.from_contents(schema)

    return Registry().with_resources(resources.items())


def validate(instance: str, schema: str) -> bool:
    """Validate an instance file in some format against a schema."""
    instance_data = load_one(instance)
    schema_data = load_one(schema)
    registry = _get_registry(Path(schema).parent)
    import jsonschema

    validator = jsonschema.Draft201909Validator(
        schema_data,
        format_checker=jsonschema.Draft201909Validator.FORMAT_CHECKER,
        registry=registry,
    )
    errors = [*validator.iter_errors(instance_data, schema_data)]
    if not errors:
        return True
    import textwrap

    cwd = Path.cwd()
    print(f"!!! {len(errors)} errors in schema validation")
    print(f"    schema:    {Path(schema).relative_to(cwd)}")
    print(f"    instance:  {Path(instance).relative_to(cwd)}")
    for error in errors:
        indent = " " * 10
        inst_text = json.dumps(error.instance, indent=2)[:120]
        print("""     - data:""")
        print(textwrap.indent(inst_text, indent))
        print(f"""       schema path: #/{"/".join(error.relative_schema_path)}""")
        print(f"""       path:        #/{"/".join(error.relative_path)}""")
        print("""       message:""")
        print(textwrap.indent(error.message, indent))
    print(f"!!! schema validation failed {len(errors)}")
    return False


def template(src: str, dest: str, **context: Any) -> None:
    import jinja2

    template = jinja2.Template(Path(src).read_text(**UTF8))
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    lines = template.render({k: v[0] for k, v in context.items()}).splitlines()
    lines = [line for line in lines if line.strip() != "#"]
    dest_path.write_text("\n".join(lines))
    load_one(dest)
