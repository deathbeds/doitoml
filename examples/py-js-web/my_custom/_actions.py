"""Python actions for ``doitoml``."""
import json
import subprocess
from hashlib import sha256
from pathlib import Path
from pprint import pformat
from typing import Generator, List, Optional, Union

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
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
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
