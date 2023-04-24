"""A base class for JSON sources."""

import json
from pathlib import Path
from typing import Any

from doitoml.errors import ParseError
from doitoml.sources._source import JsonLikeSource, Parser


class JsonSource(JsonLikeSource):
    def parse(self, data: str) -> Any:
        try:
            return json.loads(data)
        except json.JSONDecodeError as err:
            message = f"Failed to even parse {self.path}"
            raise ParseError(message) from err


class JsonParser(Parser):

    """A parser for JSON files."""

    def __call__(self, path: Path) -> JsonSource:
        """Find a JSON Source."""
        return JsonSource(path)
