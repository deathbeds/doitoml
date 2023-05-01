"""The bootstrap ``doit`` configuration for ``doitoml``."""
import sys
from typing import TYPE_CHECKING
from warnings import warn

if TYPE_CHECKING:
    from doitoml.types import Task

PIP = [sys.executable, "-m", "pip"]
PIP_INSTALL_E = [
    *PIP,
    "install",
    "-e",
    ".",
    "--no-deps",
    "--ignore-installed",
    "--no-build-isolation",
]

try:
    from doitoml import DoiTOML

    HAS_DOITOML = True
except Exception as err:
    message = f"Attempting bootstrap because: {err}"
    warn(message, stacklevel=1)
    HAS_DOITOML = False


if HAS_DOITOML:
    doitoml = DoiTOML(fail_quietly=False)
    tasks = doitoml.tasks()
    globals().update(tasks)
else:

    def task_bootstrap() -> "Task":
        """Bootstrap ``doitoml`` with an editable install."""
        return {"actions": [PIP_INSTALL_E]}
