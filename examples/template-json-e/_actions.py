"""Python actions for ``doitoml``."""
import json
from hashlib import sha256
from pathlib import Path
from typing import Generator, List, Optional, Union

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

    hashfile.write_text(output, encoding="utf-8")

    if not quiet:
        print(output)  # noqa: T201


def toml2json(src: Path, dest: Path) -> None:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib

    dest.parent.mkdir(exist_ok=True, parents=True)
    dest.write_text(
        json.dumps(
            tomllib.loads(src.read_text(encoding="utf-8")),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
