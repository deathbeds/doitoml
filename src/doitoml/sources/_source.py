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

    @abc.abstractmethod
    def read(self) -> Any:
        """Read the source exists."""

    @abc.abstractmethod
    def get(self, bits: List[Any]) -> Any:
        """Get some data from a source."""

    @abc.abstractmethod
    def parse(self, data: Any) -> Any:
        """Parse this source as something."""


class TextSource(Source):
    encoding: str

    def __init__(self, path: Path, encoding: Optional[str] = None) -> None:
        super().__init__(path)
        self.encoding = encoding or UTF8

    def read(self) -> str:
        """Read the source exists."""
        return self.path.read_text(encoding=self.encoding)


class JsonLikeSource(TextSource):

    """A class that provides access to JSON-compatible values."""

    @abc.abstractmethod
    def parse(self, data: str) -> Any:
        """Parse the data."""

    def to_dict(self) -> Dict[str, Any]:
        parsed = self.parse(self.read())
        if isinstance(parsed, dict):
            return parsed

        message = (
            f"Expected a dictionary from {self.path}, found {type(parsed)}: {parsed}"
        )
        raise ParseError(message)

    def get(self, bits: List[str]) -> Any:
        try:
            current = self.to_dict()
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
