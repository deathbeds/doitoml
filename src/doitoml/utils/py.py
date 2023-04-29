"""Utilities for using arbitrary python functions in actions, updaters, etc."""

import contextlib
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Tuple

from doitoml.errors import PyError, UnresolvedError
from doitoml.types import ExecutionContext, FnAction

from .log import call_with_capture

if TYPE_CHECKING:
    from doitoml.doitoml import DoiTOML
    from doitoml.sources._config import ConfigSource

#: a regular expression for parsing
RE_PY_DOT_FUNC = re.compile(
    r"^((?P<py_path>[^:]+?):)?((?P<dotted>[^:]+?):)((?P<func_name>[^:]+?))$",
)


def resolve_one_py_kwarg(
    doitoml: "DoiTOML",
    source: "ConfigSource",
    arg_name: str,
    arg_value: Any,
) -> Optional[Any]:
    """Resolve a single argument."""
    found_kwarg = arg_value
    if isinstance(arg_value, str):
        found_kwarg = doitoml.config.resolve_one_path_spec(
            source,
            arg_value,
            source_relative=False,
        )
    if isinstance(arg_value, list):
        found_kwarg = doitoml.config.resolve_some_path_specs(
            source,
            arg_value,
            source_relative=False,
        )[0]

    if arg_value is not None and found_kwarg is None:
        message = f"Custom Python had unresolved named arg: {arg_name}={arg_value}"
        raise UnresolvedError(message)

    return found_kwarg


def resolve_py_args(
    doitoml: "DoiTOML",
    source: "ConfigSource",
    args: List[Any],
    kwargs: Dict[str, Any],
) -> Tuple[List[Any], Dict[str, Any]]:
    """Build positional and named arguments for custom python functions."""
    if not isinstance(args, list):
        message = f"Custom Python had unusable positional arguments: {args}"
        raise PyError(message)

    if not isinstance(kwargs, dict):
        message = f"Custom Python had unusable named arguments: {kwargs}"
        raise PyError(message)

    found_args, unresolved_args = doitoml.config.resolve_some_path_specs(
        source,
        args,
        source_relative=False,
    )

    if unresolved_args:
        message = (
            f"Custom Python had unresolved positional arguments: {unresolved_args}"
        )
        raise UnresolvedError(message)

    found_kwargs = {}

    for arg_name, arg_value in kwargs.items():
        found_kwargs[arg_name] = resolve_one_py_kwarg(
            doitoml,
            source,
            arg_name,
            arg_value,
        )

    return found_args, found_kwargs


def import_dotted(
    dotted: str,
    func_name: str,
    execution_context: ExecutionContext,
    py_path: Optional[str],
) -> Any:
    """Import a named function from a module."""
    if py_path and execution_context.cwd:
        os.chdir(str(execution_context.cwd))
    current = __import__(dotted)
    for dot in dotted.split(".")[1:]:
        current = getattr(current, dot)
    return getattr(current, func_name)


def parse_dotted_py(dotted: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Parse a python importable function."""
    match = RE_PY_DOT_FUNC.search(dotted)
    if not match:  # pragma: no cover
        message = "A dotted expression was expected"
        raise PyError(message)
    groups = match.groupdict()
    return groups.get("py_path"), groups.get("dotted"), groups.get("func_name")


@contextlib.contextmanager
def patched_paths(
    execution_context: ExecutionContext,
    py_path: Optional[str] = None,
) -> Iterator:
    """Ensure the ``sys.path``, ``Path.cwd`` are correct."""
    old_env = dict(os.environ)
    os.environ.update(execution_context.env)

    new_cwd = Path.cwd().resolve()
    old_cwd = str(new_cwd)

    new_cwd = Path(execution_context.cwd).resolve()
    os.chdir(str(new_cwd))
    py_path = py_path or "."
    import_path = (new_cwd / py_path).resolve()
    old_sys_path = [*sys.path]
    sys.path = [str(import_path), *old_sys_path]

    yield

    os.chdir(str(old_cwd))
    sys.path = old_sys_path
    os.environ.clear()
    os.environ.update(old_env)


def make_py_function(
    dotted: str,
    args: List[Any],
    kwargs: Dict[str, Any],
    execution_context: ExecutionContext,
) -> FnAction:
    """Build a function that lazily imports a dotted function and calls it."""
    py_path, dotted, func_name = parse_dotted_py(dotted)

    def _py_function() -> Optional[bool]:
        with patched_paths(execution_context, py_path):
            func = import_dotted(
                str(dotted),
                str(func_name),
                execution_context,
                py_path,
            )
            result = call_with_capture(func, args, kwargs, execution_context)

        return result is not False

    return _py_function
