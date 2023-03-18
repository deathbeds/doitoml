"""Opinionated, declarative tasks for ``doit`` from well-known TOML and JSON files."""
from ._version import __version__
from .doitoml import DoiTOML

__all__ = ["__version__", "DoiTOML"]
