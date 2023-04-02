"""Domain-specific language for declarative doit task generation."""

import abc
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple, cast

from .errors import DslError
from .types import PathOrStrings

if TYPE_CHECKING:  # pragma: no cover
    from .doitoml import DoiTOML
    from .sources._config import ConfigSource


class DSL:

    """A base class for a ``doitoml`` DSL plugin."""

    #: a reference to the parent
    doitoml: "DoiTOML"

    #: the priority of the DSL
    priority = 100

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Create a DSL and remember its parent."""
        self.doitoml = doitoml

    @abc.abstractproperty
    def pattern(self) -> re.Pattern[str]:
        """Advertise the regular expression that will uniquely identify this DSL."""

    @abc.abstractmethod
    def transform_token(
        self,
        source: "ConfigSource",
        match: re.Match[str],
        raw_token: str,
    ) -> PathOrStrings:
        """Transform a token into one or more strings."""


class PathRef(DSL):

    """Look for previously-found paths."""

    priority = 80

    pattern = re.compile(r"^::((?P<prefix>[^:]+)::)?(?P<ref>[^:]+)$")

    def transform_token(
        self,
        source: "ConfigSource",
        match: re.Match[str],
        raw_token: str,
    ) -> PathOrStrings:
        """Expand a path name (with optional prefix) to a previously-found value."""
        groups = match.groupdict()
        ref: str = groups["ref"]
        prefix: str = groups["prefix"] or source.prefix
        cmds = self.doitoml.config.cmd.get((prefix, ref))
        if cmds:
            return cmds
        return self.doitoml.config.paths.get((prefix, ref))  # type: ignore


class EnvReplacer(DSL):

    """A wrapper for UNIX-style variable expansion."""

    pattern = re.compile(r"\$\{([^\}]+)\}")

    priority = 90

    def _replacer(self, match: re.Match) -> str:
        """Fetch an environment variable from the parent object."""
        return self.doitoml.get_env(match[1])

    def transform_token(
        self,
        source: "ConfigSource",
        match: re.Match[str],
        raw_token: str,
    ) -> PathOrStrings:
        """Replace all environment variable with their value in ``os.environ``."""
        return [self.pattern.sub(self._replacer, raw_token)]


class Globber(DSL):

    """A wrapper for ``glob`` and ``rglob``."""

    pattern = re.compile(r"^:(?P<kind>(r?glob))::(?P<rest>:{0,2}.*)$")

    def transform_token(
        self,
        source: "ConfigSource",
        match: re.Match[str],
        raw_token: str,
    ) -> PathOrStrings:
        """Expand a token to zero or more ~class:`pathlib.Path`s based on (r)glob(s).

        Each glob may be a matcher or have a prefix, which will be applied
        _after_ all matches occur.

        !: treated as a regular expression pattern which will exclude all matched items
        /s/: replace all occurances of each pattern with the given value
        """
        groups = match.groupdict()
        kind = cast(str, groups["kind"])
        rest = cast(str, groups["rest"])
        root, glob_rest = rest.split("::", 1)
        root_path = (source.path.parent / root).resolve()
        globs = glob_rest.split("::")
        globber = root_path.glob if kind == "glob" else root_path.rglob
        new_value: List[Path] = []
        excludes: List[re.Pattern[str]] = []
        replacers: List[Tuple[re.Pattern[str], str]] = []

        while globs:
            glob = globs.pop(0)
            if glob.startswith("!"):
                excludes += [re.compile(glob[1:])]
                continue
            if glob.startswith("/s/"):
                replacer = globs.pop(0)
                repl_value = globs.pop(0)
                replacers += [(re.compile(replacer), repl_value)]
                continue
            new_value += [*globber(glob)]

        final_value = []

        for path in new_value:
            as_posix = path.as_posix()
            if excludes:
                as_posix_rel = str(path.relative_to(source.path.parent).as_posix())
                if as_posix_rel and any(ex.search(as_posix_rel) for ex in excludes):
                    continue
            for pattern, repl_value in replacers:
                as_posix = pattern.sub(repl_value, as_posix)
            final_value += [Path(as_posix)]

        return sorted(set(final_value))


class Getter(DSL):

    """A wrapper for known parsers."""

    _pattern: re.Pattern[str]

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Initialize and pre-calculate the pattern."""
        super().__init__(doitoml)
        keys = sorted(self.doitoml.entry_points.parsers.keys())

        self._pattern = re.compile(
            r"^:get::(?P<parser>"
            + "|".join(keys)
            + r")::(?P<path>.+?)::(?P<rest>:{0,2}.*)$",
        )

    @property
    def pattern(self) -> re.Pattern[str]:
        """Load the pre-calculated pattern."""
        return self._pattern

    def transform_token(
        self,
        source: "ConfigSource",
        match: re.Match[str],
        raw_token: str,
    ) -> PathOrStrings:
        """Get a value from a parseable file, cast it to a string.

        All extra items are passed as positional arguments to the Source.
        """
        groups = match.groupdict()
        # find the parser
        parser_name: str = groups["parser"]
        parser = self.doitoml.entry_points.parsers.get(parser_name)

        if parser is None:  # pragma: no cover
            message = f"parser {parser} is not supported"
            raise DslError(message)

        path: str = groups["path"]
        bits = groups["rest"].split("::")
        get_path = (source.path.parent / path).resolve()

        if not get_path.exists():
            message = f"{get_path} does not exist, can't get {bits}"
            raise DslError(message)

        new_value = parser(get_path).get(bits)

        if isinstance(new_value, str):
            return [new_value]

        if isinstance(new_value, dict):
            return [json.dumps(new_value)]

        return [x if isinstance(x, str) else json.dumps(x) for x in new_value]
