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
    dumped = doitoml.config.to_dict()
    dumped["env"] = doitoml.config.env
    display(JSON(dumped))

def mm_task(n):
    return f"{n}[/{n}/]"
        
def mm_files(t, fld):
    return [f"{f}({f})" for f in t.get(fld, [])]

def mm_task_line(n, t):
    n = n[1:] if n.startswith(":") else n
    tsk = mm_task(n)
    dep = " & ".join([*map(mm_task, t.get("task_dep", [])), *mm_files(t, "file_dep")])
    tgt = " & ".join(mm_files(t, "targets"))
    arr = " --> "
    return f"""{dep + arr if dep else ""}{tsk}{arr + tgt if tgt else ""}"""


def mermaid():
    dt = doitoml.config.to_dict()
    lines = [mm_task_line(n, t) for n, t in dt["tasks"].items()]
    display(Markdown("\n".join(["```mermaid", "flowchart LR", *lines, "```"])))
            
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
    DoitMain.BIN_NAME = "doit"
    DoitMain().run(shlex.split(line))
