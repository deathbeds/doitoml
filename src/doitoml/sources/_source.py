"""Base classes for sources and parsers."""
import abc
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from doitoml.constants import UTF8
from doitoml.errors import DoitomlError, ParseError

if TYPE_CHECKING:
    from doitoml.doitoml import DoiTOML


class Source:

    """Base class for a source."""

    path: Path

    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> Any:
        """Read the source exists."""
        return self.path.read_bytes()

    @abc.abstractmethod
    def get(self, bits: List[Any]) -> Any:
        """Get some data from a source."""


class TextSource(Source):
    encoding: str

    def __init__(self, path: Path, encoding: Optional[str] = None) -> None:
        super().__init__(path)
        self.encoding = encoding or UTF8


class JsonLikeSource(TextSource):

    """A class that provides access to JSON-compatible values."""

    @abc.abstractmethod
    def parse(self) -> Dict[str, Any]:  # pragma: no cover
        """Parse this source as a dictionary."""

    def get(self, bits: List[str]) -> Any:
        try:
            current = self.parse()
        except DoitomlError as err:
            message = f"{self.__class__.__name__} failed to parse {self.path}: {err}"
            raise ParseError(message) from err
        for bit in bits:
            try:
                if isinstance(current, dict):
                    current = current[bit]
                    continue
                if isinstance(current, (list, tuple, str)):
                    current = current[json.loads(bit)]
                    continue
            except KeyError:
                pass
            message = f"Can't parse {bit} of {bits} from {self.path}: {current}"
            raise ParseError(message)
        return current


class Parser:

    """A parser that loads sources."""

    doitoml: "DoiTOML"

    #: the order in which parsers are checked (lowest-first)
    rank = 100

    def __init__(self, doitoml: "DoiTOML") -> None:
        self.doitoml = doitoml

    @abc.abstractmethod
    def __call__(self, path: Path) -> Source:  # pragma: no cover
        """Load a source from a path."""
