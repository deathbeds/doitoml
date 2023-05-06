"""A lightweight magic for demos."""
import shlex
import sys
import types

import IPython

LITE = "pyodide" in sys.modules

if LITE:
    dbm = sys.modules["dbm"] = types.ModuleType("dbm")
    dbm.dumb = True
    dbm.error = None
    dbm.whichdb = lambda: None
    del dbm


@IPython.core.magic.register_line_magic
def doitoml(line):
    from doit.doit_cmd import DoitMain

    DoitMain().run(shlex.split(line))
