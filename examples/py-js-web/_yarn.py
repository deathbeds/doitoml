"""A wrapper for the yarn package manager.

Copied from:

https://raw.githubusercontent.com/jupyterlab/jupyterlab/master/jupyterlab/jlpmapp.py
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""

import os
from pathlib import Path
import subprocess
import sys
from shutil import which

NODE_PATH = which("node") or which("node.exe") or which("node.cmd") or which("node.bat")

YARN_PATH = which("yarn") or which("yarn.cmd") or which("yarn.exe") or which("yarn.bat")

YARN_JS_PATH = Path(YARN_PATH).parent / "yarn.js"


def execvp(cmd, argv):
    """Execvp, except on Windows where it uses Popen.

    The first argument, by convention, should point to the filename
    associated with the file being executed.

    Python provides execvp on Windows, but its behavior is problematic
    (Python bug#9148).
    """
    if os.name == "nt":
        import signal
        import sys

        p = subprocess.Popen([cmd] + argv[1:])
        # Don't raise KeyboardInterrupt in the parent process.
        # Set this after spawning, to avoid subprocess inheriting handler.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        p.wait()
        sys.exit(p.returncode)
    else:
        os.execvp(cmd, argv)


def main(argv=None):
    """Run node and return the result."""
    # Make sure node is available.
    argv = argv or sys.argv[1:]
    execvp(NODE_PATH, [NODE_PATH, YARN_JS_PATH, *argv])


if __name__ == "__main__":
    main()
