"""A base class for JSON sources."""

import json
from pathlib import Path
from typing import Any, List

from doitoml.errors import DoitomlError, ParseError
from doitoml.sources._source import Parser, Source


class JsonSource(Source):
    def parse(self) -> Any:
        return json.loads(self.read())

    def get(self, bits: List[Any]) -> Any:
        """Get a named value from the source."""
        try:
            current = self.parse()
        except DoitomlError as err:
            message = f"{self.__class__.__name__} failed to parse {self.path}: {err}"
            raise ParseError(message) from err
        for bit in bits:
            if isinstance(current, (dict, list, tuple, str)):
                current = current[bit]
        return current


class JsonParser(Parser):

    """A parser for JSON files."""

    def __call__(self, path: Path) -> JsonSource:
        """Find a JSON Source."""
        return JsonSource(path)
