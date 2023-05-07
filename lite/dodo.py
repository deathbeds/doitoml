"""while not strictly _neccessary_, a `dodo.py` is a nice, conventional place
to put extra actions.
"""
import shlex
import platform
import types
import sys
from collections import defaultdict
import IPython
from IPython.display import JSON, Markdown, display
from pathlib import Path
from datetime import datetime

LITE = platform.machine() == "wasm32"

if LITE:
    dbm = sys.modules["dbm"] = types.ModuleType("dbm")
    dbm.dumb = True
    dbm.error = None
    dbm.whichdb = lambda: None
    del dbm

# with the patch in place, we can import the rest
if True:
    from doitoml import DoiTOML

doitoml = DoiTOML()
globals().update(doitoml.tasks())

def greet(whom):
    print(f"# Hello {whom}")
    print(f"> Generated at {datetime.now().isoformat()}")
    return True


def dump():
    dumped = doitoml.config.to_dict()
    dumped["env"] = doitoml.config.env
    display(JSON(dumped))

def mm_task(n):
    return f"""{n}[/"▶️ {n}"/]"""

def mm_sources(dt_dict):
    sources = defaultdict(list)
    lines = []
    for n, t in dt_dict["tasks"].items():
        n = n[1:] if n.startswith(":") else n
        sources[t["meta"]["doitoml"]["source"]] += [n]
    common_parent = sorted(sources, key=lambda x: len(x))[0]
    prefix = common_parent.rsplit("/", 1)[0] + "/"
    for source, tasks in sources.items():
        lines += [
            f"""subgraph {source.replace(prefix, "")}""",
            *[mm_task(n) for n in tasks],
            "end"
        ]
    return lines

def mm_files(t, fld):
    return [f"""{f}("📄 {f.split("/")[-1]}")""" for f in t.get(fld, [])]

def mm_task_line(n, t):
    n = n[1:] if n.startswith(":") else n
    tsk = mm_task(n)
    dep = " & ".join([*map(mm_task, t.get("task_dep", [])), *mm_files(t, "file_dep")])
    tgt = " & ".join(mm_files(t, "targets"))
    arr = " --> "
    return f"""{dep + arr if dep else ""}{tsk}{arr + tgt if tgt else ""}"""

def dt2mermaid(dt_dict, direction="LR"):
    lines = mm_sources(dt_dict)
    lines += [mm_task_line(n, t) for n, t in dt_dict["tasks"].items()]
    return "\n".join(["```mermaid", f"flowchart {direction}", *lines, "```"])

def mermaid():
    display(Markdown(dt2mermaid(doitoml.config.to_dict())))


@IPython.core.magic.register_line_magic
def doit(line):
    """`%doit` emulates the ``doit`` CLI"""
    from doit.doit_cmd import DoitMain
    DoitMain.BIN_NAME = "doit"
    DoitMain().run(shlex.split(line))

@IPython.core.magic.register_line_magic
def md(line):
    """`%md` prints out the given markdown file"""
    display(Markdown(Path(line.strip()).read_text(encoding="utf-8")))
