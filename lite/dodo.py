"""while not strictly _neccessary_, a `dodo.py` is a nice, conventional place
to put extra actions.
"""
# first install doitoml
from doitoml import DoiTOML

doitoml = DoiTOML()
globals().update(doitoml.tasks())

# then regular business
from IPython.display import JSON, Markdown, display


def greet(whom):
    print(f"Hello {whom}")
    return True


def dump():
    display(JSON(doitoml.config.to_dict()))


def mermaid():
    dt = doitoml.config.to_dict()
    mermaid = ["flowchart LR"]
    for name, t in dt["tasks"].items():
        line = name[1:] if name.startswith(":") else name
        dep = " & ".join([*t.get("task_dep", []), *t.get("file_dep", [])])
        " & ".join([*t.get("targets", [])])
        line = line if not dep else f"{dep} --> {line}"
        mermaid += [line]
    display(Markdown("\n".join(["```mermaid", *mermaid, "```"])))

# the magic
import shlex
import sys
import platform
import types

import IPython

LITE = platform.machine() == "wasm32"

if LITE:
    dbm = sys.modules["dbm"] = types.ModuleType("dbm")
    dbm.dumb = True
    dbm.error = None
    dbm.whichdb = lambda: None
    del dbm


@IPython.core.magic.register_line_magic
def doit(line):
    from doit.doit_cmd import DoitMain

    DoitMain().run(shlex.split(line))
