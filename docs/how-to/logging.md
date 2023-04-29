# Logging

`doit` offers rudimentary control with the top- and task-level `verbosity` setting, but
this only controls the output observed on the console.

Task actions often create useful outputs, but may not all provide a way to write their
output to files, which sometimes leads to convoluted shell redirection, which can be
inconsistent on different platforms, especially Windows.

A few utilities are provided to manage writing action outputs to files, which can then
be used as `file_dep` of other tasks.

## Write all task output to a file

An example of a useful output is a `requirements.txt`

```toml
# pyproject.toml
[tool.doitoml.paths]
pip_freeze = "build/pip-freeze.txt"

[tool.doitoml.tasks.pip]
meta = {doitoml = {log = "::pip_freeze"}}
actions = [["pip", "freeze"]]
targets = ["::pip_freeze"]
```

```{note}
This approach also works for [user Python actions](./user-python.md).
```

## Splitting output streams

Some scripts generate useful output on the `stdout` stream and diagnostics and warnings
on `stderr`. These can be separately configured. As `null` is not a valid value in TOML,
the empty string can be given to let output be streamed to the console, or only shown on
error, as configured by `doit`'s `verbosity`.

```toml
# pyproject.toml
[tool.doitoml.paths]
cmd_output = "build/cmd-output.txt"

[tool.doitoml.tasks.some]
meta = {doitoml = {log = ["::cmd_output", ""]}}
actions = [["some-command"]]
targets = ["::cmd_output"]
```
