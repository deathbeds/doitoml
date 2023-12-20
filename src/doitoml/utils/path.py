"""Utilities for working with paths."""

from pathlib import Path
from typing import Optional, Tuple

from doitoml.types import PathOrString


def ensure_parents(*paths: Optional[Path]) -> Tuple[Optional[Path], ...]:
    """Clean out some paths and ensure their parents."""
    for path in paths:
        if not path:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
    return paths


def normalize_path(path: PathOrString) -> str:
    """Apply some best-effort, platform-aware path normalization."""
    as_path = Path(path).resolve()
    norm = as_path.as_posix()
    if as_path.drive:  # pragma: no cover
        norm_bits = str(path).split(":")
        norm = ":".join([norm_bits[0].lower(), *norm_bits[1:]])
    return norm
