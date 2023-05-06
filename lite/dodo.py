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
        line = name
        dep = " & ".join([*t.get("task_dep", []), *t.get("file_dep", [])])
        " & ".join([*t.get("targets", [])])
        line = line if not dep else f"{dep} --> {line}"
        mermaid += [line]
    display(Markdown("\n".join(["```mermaid", *mermaid, "```"])))
