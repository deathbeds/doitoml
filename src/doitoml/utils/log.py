"""Utilities for logging.."""

import contextlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from doitoml.types import ExecutionContext

from .path import ensure_parents


def call_with_capture(
    func: Callable[[Any], Optional[bool]],
    args: List[Any],
    kwargs: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Optional[bool]:
    """Call a function with optional output capturing."""
    stdout, stderr = ensure_parents(*execution_context.log_paths)

    stdout_mgr: contextlib.AbstractContextManager = contextlib.nullcontext()
    stderr_mgr: contextlib.AbstractContextManager = contextlib.nullcontext()

    managers: List[contextlib.AbstractContextManager] = []
    if isinstance(stdout, Path):
        stdout_fh = stdout.open(execution_context.log_mode)
        stdout_mgr = contextlib.redirect_stdout(stdout_fh)
        managers += [stdout_mgr]
    if isinstance(stderr, Path):
        if stderr == stdout:
            stderr_mgr = contextlib.redirect_stderr(stdout_fh)
        else:
            stderr_fh = stderr.open(execution_context.log_mode)
            stderr_mgr = contextlib.redirect_stderr(stderr_fh)
        managers += [stderr_mgr]

    with stdout_mgr, stderr_mgr:
        return func(*args, **kwargs)
