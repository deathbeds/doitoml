"""Python actions for ``doitoml``."""
from typing import List, Union
from pathlib import Path

def hash_files(hashfile: "Path", files: List[Union["Path", str]]) -> None:
    """Emulate ``sha256sum`` to write out a file."""
    from hashlib import sha256

    hashfile = hashfile[0]

    if hashfile.exists():
        hashfile.unlink()

    lines = [
        f"{sha256(Path(p).read_bytes()).hexdigest()}  {Path(p).name}"
        for p in sorted(files)
    ]

    output = "\n".join(lines) + "\n"
    print(output)
    hashfile.write_text(output, encoding="utf-8")
