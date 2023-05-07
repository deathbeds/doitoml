"""User-defined Python skippers."""
import json
import platform
import re
from typing import TYPE_CHECKING, Any

from doitoml.errors import PyError, SkipError
from doitoml.skippers._skipper import Skipper
from doitoml.types import ExecutionContext
from doitoml.utils.py import make_py_function, resolve_py_args

if TYPE_CHECKING:
    from doitoml.sources._config import ConfigSource


class Platform(Skipper):

    """A skipper that skips if the given value from Python's ``platform`` matches."""

    def should_skip(self, source: "ConfigSource", skip: Any) -> bool:
        """Skip if (any) given path does not exist."""
        if not isinstance(skip, dict):
            message = f"{source} Cannot skip `platform`: {skip}"
            raise SkipError(message)

        if len(skip) > 1:
            message = f"{source} can only skip based on one `platform`: {skip}"
            raise SkipError(message)

        key, pattern = list(skip.items())[0]

        func = getattr(platform, key, None)

        if not callable(func):
            message = f"{source} cannot skip based on `platform.{key}`"
            raise SkipError(message)

        value = func()
        value = value if isinstance(value, str) else json.dumps(value)
        return re.match(pattern, value) is not None


class Py(Skipper):

    """A user-defined Python function skipper."""

    def should_skip(self, source: "ConfigSource", skip: Any) -> bool:
        """Skip if a user-defined python function is falsey."""
        if not isinstance(skip, dict):  # pragma: no cover
            message = f"{source} provided unknown skip args {skip}"
            raise PyError(message)
        path_dotted_func, args_kwargs = list(skip.items())[0]
        args, kwargs = resolve_py_args(
            self.doitoml,
            source,
            args_kwargs.pop("args", []),
            args_kwargs.pop("kwargs", {}),
        )
        args_kwargs.update(args=args, kwargs=kwargs)
        args, kwargs = args_kwargs["args"], args_kwargs["kwargs"]
        # TODO: improve
        execution_context = ExecutionContext(
            cwd=source.path.parent,
            env={},
            log_mode="w",
            log_paths=(None, None),
        )
        py_func = make_py_function(
            path_dotted_func,
            args,
            kwargs,
            execution_context,
        )
        return bool(py_func())
