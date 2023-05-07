"""Domain-specific language for declarative ``doit`` task generation."""

import abc
import fnmatch
import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, cast

from doitoml.constants import FNMATCH_WILDCARDS

from .errors import DslError
from .types import Strings

if TYPE_CHECKING:
    from .doitoml import DoiTOML
    from .sources._config import ConfigSource
    from .sources._source import Source


class DSL:

    """A base class for a ``doitoml`` DSL plugin."""

    #: a reference to the parent
    doitoml: "DoiTOML"

    #: the rank of the DSL
    rank = 100

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
        **kwargs: Any,
    ) -> Strings:
        """Transform a token into one or more strings."""


class PathRef(DSL):

    """Look for previously-found paths."""

    #: paths go before all other built-in DSL
    rank = 80

    pattern = re.compile(r"^::((?P<prefix>[^:]*)::)?(?P<ref>[^:]+)$")

    def transform_token(
        self,
        source: "ConfigSource",
        match: re.Match[str],
        raw_token: str,
        **kwargs: Any,
    ) -> Strings:
        """Expand a path name (with optional prefix) to a previously-found value."""
        groups = match.groupdict()
        ref: str = groups["ref"]
        prefix = source.prefix if groups["prefix"] is None else groups["prefix"]

        config = self.doitoml.config

        if any(c in prefix for c in FNMATCH_WILDCARDS):
            prefixes = fnmatch.filter(sorted(config.sources), prefix)
        else:
            prefixes = [prefix]

        prefix_tokens: Dict[str, List[str]] = {}

        for prefix in prefixes:
            for named in [config.paths, config.tokens]:
                from_named = named.get((prefix, ref))
                if from_named is not None:
                    prefix_tokens[prefix] = from_named

        if prefix_tokens:
            return sum(prefix_tokens.values(), [])

        return None  # type: ignore


class EnvReplacer(DSL):

    """A wrapper for UNIX-style variable expansion."""

    pattern = re.compile(r"\$\{([^\}]+)\}")

    #: paths go before most other built-in DSL
    rank = 90

    def _replacer(self, match: re.Match) -> str:
        """Fetch an environment variable from the parent object."""
        return self.doitoml.get_env(match[1])

    def transform_token(
        self,
        source: "ConfigSource",
        match: re.Match[str],
        raw_token: str,
        **kwargs: Any,
    ) -> Strings:
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
        **kwargs: Any,
    ) -> Strings:
        """Expand a token to zero or more :class:`pathlib.Path` based on (r)glob(s).

        Chunks are delimited by ``::``. The first chunk is a relative path.

        Each following chunk between ``::`` may be a matcher or have a prefix.

        - ``!``: a :class:`re.Pattern` which will exclude all matched items
        - ``/s/``: expects two following chunks:

          - the first is a :class:`re.Pattern` to `find`
          - the next is the `replacement` string

        Order does not matter: all excludes an replacers will be applied `after`
        all matches are expanded.
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

        parent_posix = source.path.parent.as_posix()

        for path in new_value:
            as_posix = path.as_posix()
            if excludes:
                as_posix_rel = Path(
                    os.path.relpath(str(as_posix), parent_posix),
                ).as_posix()
                if as_posix_rel and any(ex.search(as_posix_rel) for ex in excludes):
                    continue
            for pattern, repl_value in replacers:
                as_posix = pattern.sub(repl_value, as_posix)
            final_value += [as_posix]

        return sorted(set(final_value))


class Getter(DSL):

    """A wrapper for known parsers."""

    _pattern: re.Pattern[str]

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Initialize and pre-calculate the pattern."""
        super().__init__(doitoml)
        keys = sorted(self.doitoml.entry_points.parsers.keys())

        self._pattern = re.compile(
            r"^:get(?P<default>\|[^:]*)?::(?P<parser>"
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
        **kwargs: Any,
    ) -> Strings:
        """Get a value from a parseable file, cast it to a string.

        All extra items are passed as positional arguments to the Source.
        """
        try:
            new_source, bits = self.get_source_with_key(source, match, raw_token)
        except DslError as err:
            default = match.groupdict()["default"]
            if default:
                return [default[1:]]
            raise err

        new_value = new_source.get(bits)

        if isinstance(new_value, str):
            return [new_value]

        if isinstance(new_value, dict):
            return [json.dumps(new_value)]

        if isinstance(new_value, (int, float, bool)):
            return [json.dumps(new_value)]

        return [x if isinstance(x, str) else json.dumps(x) for x in new_value]

    def get_source_with_key(
        self,
        source: "ConfigSource",
        match: re.Match[str],
        raw_token: str,
    ) -> Tuple["Source", List[str]]:
        """Find a raw source and its bits."""
        groups = match.groupdict()
        path: str = groups["path"]
        groups["default"]
        bits: List[str] = groups["rest"].split("::")
        if len(bits) == 1 and not bits[0]:
            bits = []
        # find the parser
        parser_name: str = groups["parser"]
        parser = self.doitoml.entry_points.parsers.get(parser_name)

        if parser is None:  # pragma: no cover
            message = f"parser {parser} is not supported"
            raise DslError(message)

        get_path = (source.path.parent / path).resolve()

        if not get_path.exists():
            message = f"{get_path} does not exist, can't get {bits}"
            raise DslError(message)
        new_source = parser(get_path)
        return new_source, bits
