"""Custom loaders for doit tasks."""
from typing import Any, Dict

from doit.cmd_base import DodoTaskLoader

from .doitoml import DoiTOML


class DoitomlLoader(DodoTaskLoader):

    """A `doit` task loader with a ``DoiTOML``."""

    doitoml: DoiTOML


class PyprojectTomlLoader(DoitomlLoader):

    """A loader that only discovers tasks in `pyproject.toml`."""

    def setup(self, opt_values: Dict[str, Any]) -> None:
        """Discover tasks in ``pyproject.toml``."""
        self.doitoml = DoiTOML(cwd=opt_values["cwdPath"])
        self.namespace = self.doitoml.tasks()


class PackageJsonLoader(DoitomlLoader):

    """A loader that only discovers tasks in `package.json`."""

    def setup(self, opt_values: Dict[str, Any]) -> None:
        """Discover tasks in ``package.json.toml``."""
        self.doitoml = DoiTOML(["package.json"], cwd=opt_values["cwdPath"])
        self.namespace = self.doitoml.tasks()


class DodoPyprojectLoader(DoitomlLoader):

    """A loader that discovers tasks in ``dodo.py`` and then ``pyproject.toml``."""

    def setup(self, opt_values: Dict[str, Any]) -> None:
        """Discover tasks in ``dodo.py``, then in ``pyproject.toml``."""
        super().setup(opt_values)
        self.doitoml = DoiTOML(["pyproject.toml"], cwd=opt_values["cwdPath"])
        self.namespace.update(self.doitoml.tasks())
