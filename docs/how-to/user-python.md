# User-defined Python

While the baseline `doit` and `doitoml` features work very well for running well-known
CLI functions with _tokens_ or raw _shell_ actions, sometimes a little programmability
can go a long, portable way.

## Use a Python function as an action

The `py` action offers user-defined importable Python names for actions, using the
`entry_point` notation of `module.submodule:function`.

The imported function must return `None` or `True` on _success_. A return value of
`False`, or any raised `Exception`, is considered a _failure_, and any other return
value is an _error_.

Many Python `stdlib` functions that accept simple, JSON-compatible values work out of
the box.

````{tab-set}

  ~~~{tab-item} pyproject.toml
  ```toml
  [tool.doitoml.tasks.copy]
  actions = [
      {py = {"shutil:copytree" = {kwargs = {src = "from/path/", dst = "to/path"} } }
  ]
  ```
  ~~~

  ~~~{tab-item} package.json
  ```json
  {
    "doitoml": {
      "tasks": {
        "copy": {
          "actions": {
            "py": {
              "shutil:copytree": {
                "kwargs": {"src": "from/path/", "dst": "to/path/"}
              }
            }
          }
        }
      }
    }
  }
  ```
  ~~~

````

## Use a Python function as an up-to-date checker

When capturing paths in `file_dep` and `targets`, or the various built-in `doit.tools`
functions like `config_changed`, `run_once` are insufficient, custom python functions
may also be used as up-to-date checkers.

For example, with a project layout like...

```
./
  ├─ pyproject.toml
  └─ my_checkers.py
```

...where some checkers are defined in `my_checkers.py`:

```py
# my_checkers.py
from datetime import datetime

def is_weekend():
    return datetime.now().isoweekday() > 5
```

...a task can reference this checker in `uptodate`:

```toml
# child/pyproject.toml
[tool.doitoml.tasks.greet]
uptodate = [{py={"my_checkers:is_weekend" = {}}}]
actions = [["echo", "hello", "weekday"]]
```

## Finding importable functions

By default, `doit` will put the current working directory on Python's `sys.path`,
meaning any importable name will be available.

```{warning}
Be careful with naming modules in a way that would overload Python's standard library!
```

For example, with a simple project layout like:

```
./
  ├─ pyproject.toml
  └─ my_actions.py
```

A where `my_actions.py` defines one function:

```python
# my_actions.py
def greet(greeting: str, *greeted: List[str]):
    print(greeting, *greeted)
```

Can be referenced as:

```toml
# pyproject.toml
[tool.doitoml.tasks.greet]
actions = [
    {py = {"my_actions:greet" = {args = ["hello", "world"] } }
]
```

### `sys.path`

In more complex projects, the simple path hack may not be sufficient, and can be further
customized by prepending the importable name with an additional `{path}:`.

For example, with a project layout like:

```
./
  ├─ pyproject.toml
  ├─ child/
  │  └─ pyproject.toml
  └─ my_actions
      ├─ __init__.py
      └─ greetings.py
```

The `pyproject.toml` in the `child` directory can extend `sys.path` to find the
`greetings` module:

```toml
# child/pyproject.toml
[tool.doitoml.tasks.greet]
actions = [
    {py = {"../my_actions:greetings:greet" = {args = ["hello", "world"] } }
]
```

### Importing `dodo`

In a project with `doit`'s default `dodo.py` layout, the `dodo` module itself can be
imported...

```toml
# pyproject.toml
[tool.doitoml.tasks.greet]
actions=[{ py = {"dodo:greet": { kwargs = { whom = "world" } } } }]

[tool.doitoml.tasks.greet]
actions=[{ py = {"dodo:dump": { } } }]
```

... and even explore a `DoiTOML` instance.

```py
# dodo.py
from doitoml import DoiTOML
doitoml = DoiTOML()
globals().update(doitoml.tasks())

def greet(whom):
    print(f"Hello {whom}")
    return True

def dump():
    from pygments import highlight
    from pygments.lexers import YamlLexer
    from pygments.formatters import TerminalFormatter
    from yaml import safe_dump
    print(
        highlight(
            safe_dump(doitoml.config.to_dict()),
            YamlLexer(),
            TerminalFormatter(bg="dark")
        )
    )
```
