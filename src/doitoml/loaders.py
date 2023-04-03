"""Custom loaders for doit tasks."""
from pathlib import Path
from typing import Any, Dict

from doit.cmd_base import DodoTaskLoader

from .doitoml import DoiTOML


class DoitomlLoader(DodoTaskLoader):

    """A loader that looks for all known config files."""

    doitoml: DoiTOML

    def setup(self, opt_values: Dict[str, Any]) -> None:
        """Discover tasks in all config files."""
        cwd = Path(opt_values["cwdPath"]) if opt_values["cwdPath"] else Path.cwd()

        self.doitoml = DoiTOML(cwd=opt_values["cwdPath"], discover_config_paths=True)

        if (cwd / "dodo.py").exists():
            super().setup(opt_values)

        tasks = self.doitoml.tasks()

        if getattr(self, "namespace", None):
            self.namespace.update(tasks)  # type: ignore
        else:
            self.namespace = tasks
