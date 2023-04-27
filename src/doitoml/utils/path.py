"""Utilities for working with paths."""

from pathlib import Path
from typing import Optional, Tuple


def ensure_parents(*paths: Optional[Path]) -> Tuple[Optional[Path], ...]:
    """Clean out some paths and ensure their parents."""
    for path in paths:
        if not path:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
    return paths
