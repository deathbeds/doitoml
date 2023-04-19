# Cheatsheet

## `doit` CLI invocations

| command                           | example                  | command description                       |
| --------------------------------- | ------------------------ | ----------------------------------------- |
| `doit`                            | `doit`                   | run all default tasks                     |
| `doit {task name} [task name...]` | `doit build test`        | run named tasks (generally in order)      |
| `doit [*]{task fragment}[*]`      | `doit lint*py`           | run tasks matching a pattern              |
| `doit list`                       | `doit list --all-status` | show all top level tasks                  |
| `doit info {task name}`           | `doit info test`         | show full information about a single task |
| `doit forget {task name}`         | `doit forget build`      | reset a task's `run` status               |

## `doit` tasks

> Put these in `doitoml.tasks.{task name}` to do things.

| field title     | `doit` command | field data type                                | field description                                                               |
| --------------- | :------------: | ---------------------------------------------- | ------------------------------------------------------------------------------- |
| **`actions`**   |     `run`      | list of (_string_ or _list of strings_)        | the _shell_, _token_ or _function_ actions to peform                            |
| **`name`**      |     _all_      | string                                         | identifier for `doit run`, etc.                                                 |
| **`doc`**       | `list`, `info` | string                                         | diplayed with `doit list` and `info`                                            |
| **`file_dep`**  |     `run`      | `run` list of strings or `Path`                | file dependencies which, if changed, invalidate a task status                   |
| **`targets`**   |     `run`      | list of strings or `Path`                      | files created by a task                                                         |
| **`title`**     |     `run`      | string or function                             | extra information to print with `doit run`                                      |
| **`task_dep`**  |     `run`      | list of strings                                | other task ids which must have been run once before this tasks                  |
| **`uptodate`**  |     `run`      | list of `bool` or functions                    | extra data which, if all false, invalidate a task status                        |
| **`clean`**     |    `clean `    | `bool` or list of strings or paths or function | files to delete with `doit clean` (true cleans all `targets`)                   |
| **`verbosity`** |     `run`      | `int`                                          | custom verbosity: `0` only print on failures, `1` stream errors, `2` stream all |
| **`meta`**      |     `run`      | dict                                           | [custom metadata](#doitoml-task-metadata) for tasks                             |

<details>

<summary><b>Why these fields? What about...</b></summary>

> The [pydoit documentation](https://pydoit.org/tasks.html) provides a number of other fields: many of these only make sense in a `dodo.py`, or otherwise don't lend themselves cleanly to declarative, portable tasks.

</details>

### `actions`

| action kind | example                                | description                                          |
| ----------- | -------------------------------------- | ---------------------------------------------------- |
| _string_    | `echo 1`                               | passed directly to `doit` without any manipulation   |
| _token_     | `["echo", "1"]`                        | each token expanded by the [DSL](./dsl.md)           |
| _actor_     | `{py="shutil.copy2", args=["a", "b"]}` | each token in `args` expanded by the [DSL](./dsl.md) |

### `doitoml` task metadata

> Put these in your `task.{task name}.meta.doitoml` to fune-tune the behavior of tasks.

| field title | field data type       | field description                                                                  |
| ----------- | --------------------- | ---------------------------------------------------------------------------------- |
| **`cwd`**   | string or `Path`      | the current working directory for _shell_, _token_, and _actor_ tasks              |
| **`env`**   | dictionary of strings | environment variables to overload for a specific task                              |
| **`skip`**  | string or `bool`      | if _falsey_, this task will not appear in `doit list` or be included in `doit run` |
| **`tee`**   | string or `Path`      | file to capture `stodut` and `stderr`                                              |