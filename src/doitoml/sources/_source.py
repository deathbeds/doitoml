"""Base classes for sources and parsers."""
import abc
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from doitoml.constants import UTF8
from doitoml.errors import ParseError

if TYPE_CHECKING:  # pragma: no cover
    from doitoml.doitoml import DoiTOML


class Source:

    """Base class for a source."""

    path: Path

    def __init__(self, path: Path) -> None:
        self.path = path

    def exists(self) -> bool:
        """Determine if the source exists."""
        return self.path.exists()

    def read(self) -> Any:
        """Read the source exists."""
        return self.path.read_bytes()

    def get(self, bits: List[str]) -> Any:
        """Get a named value from the source."""
        message = f"{self.__class__} cannot get {bits}"
        raise NotImplementedError(message)


class TextSource(Source):
    encoding: str

    def __init__(self, path: Path, encoding: Optional[str] = None) -> None:
        super().__init__(path)
        self.encoding = encoding or UTF8

    @abc.abstractmethod
    def get(self, bits: List[Any]) -> Any:
        """Get some data from a source."""


class DictSource(TextSource):
    @abc.abstractmethod
    def parse(self) -> Dict[str, Any]:
        """Parse this source as a dictionary."""

    def get(self, bits: List[str]) -> Any:
        try:
            current = self.parse()
        except Exception as err:
            message = f"{self.__class__.__name__} failed to parse {self.path}: {err}"
            raise ParseError(message) from err
        for bit in bits:
            if isinstance(current, (dict, list, tuple, str)):
                current = current[bit]
        return current


class Parser:

    """A parser that loads sources."""

    doitoml: "DoiTOML"

    priority = 100

    def __init__(self, doitoml: "DoiTOML") -> None:
        self.doitoml = doitoml

    @abc.abstractmethod
    def __call__(self, path: Path) -> Source:
        """Load a source from a path."""
