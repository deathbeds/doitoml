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

| field title     | `doit` command | field data type                                | field description                                                                 |
| --------------- | :------------: | ---------------------------------------------- | --------------------------------------------------------------------------------- |
| **`actions`**   |     `run`      | list of (_string_ or _list of strings_)        | the _shell_, _token_ or _function_ actions to peform                              |
| **`name`**      |     _all_      | string                                         | identifier for `doit run`, etc.                                                   |
| **`doc`**       | `list`, `info` | string                                         | diplayed with `doit list` and `info`                                              |
| **`file_dep`**  |     `run`      | `run` list of strings or `Path`                | file dependencies which, if changed, invalidate a task status                     |
| **`targets`**   |     `run`      | list of strings or `Path`                      | files created by a task                                                           |
| **`title`**     |     `run`      | string or function                             | extra information to print with `doit run`                                        |
| **`task_dep`**  |     `run`      | list of strings                                | other task ids which must have been run once before this task: uses `*` wildcards |
| **`uptodate`**  |     `run`      | list of `bool` or functions                    | extra data which, if all false, invalidate a task status                          |
| **`clean`**     |    `clean `    | `bool` or list of strings or paths or function | files to delete with `doit clean` (true cleans all `targets`)                     |
| **`verbosity`** |     `run`      | `int`                                          | custom verbosity: `0` only print on failures, `1` stream errors, `2` stream all   |
| **`meta`**      |     `run`      | dict                                           | [custom metadata](#doitoml-task-metadata) for tasks                               |
| **`uptodate`**  |     `run`      | list of (string, `None`, dict)                 | string shell commands or custom updaters indicating a task is up-to-date          |

<details>

<summary><b>Why these fields? What about...</b></summary>

> The [pydoit documentation](https://pydoit.org/tasks.html) provides a number of other
> fields: many of these only make sense in a `dodo.py`, or otherwise don't lend
> themselves cleanly to declarative, portable tasks.

</details>

## `actions`

| action kind | TOML example                                        | description                                        |
| ----------- | --------------------------------------------------- | -------------------------------------------------- |
| _string_    | `echo 1`                                            | passed directly to `doit` without any manipulation |
| _token_     | `["echo", "1"]`                                     | each token expanded by the [DSL]                   |
| _actor_     | `{py={"shutil.copy2"={args=["a"], kwargs={b="c"}}}` | each token in `(kw)args` expanded by the [DSL]     |

## `doitoml` task metadata

> Put these in your `task.{task name}.meta.doitoml` to fune-tune the behavior of tasks.

| field title | field data type            | field description                                                                                 |
| ----------- | -------------------------- | ------------------------------------------------------------------------------------------------- |
| **`cwd`**   | string or `Path`           | the current working directory for _shell_, _token_, and _actor_ tasks                             |
| **`env`**   | dictionary of strings      | environment variables to overload for a specific task                                             |
| **`skip`**  | string or `bool` or dict   | if _falsey_, this task will not appear in `doit list` or be included in `doit run`                |
| **`log`**   | (list of) string or `Path` | file(s) to capture output of actions, e.g. `task.log` or `["task.stdout.log", "task.stderr.log"]` |

## `skip` values

`skip` uses simple, normalized JSON `bool`-like values directly.

More complex behaviors can be built from dictionary-based values.

| skip kind      | true TOML example                   | will skip if...                    |
| -------------- | ----------------------------------- | ---------------------------------- |
| **`any`**      | `{any=[0, "TRUE"]}`                 | _any_ value is truthy              |
| **`all`**      | `{all=[1, "${A_TRUE_ENV_VAR}"]}`    | _all_ values is truthy             |
| **`not`**      | `{not=0}`                           | the value is falsey                |
| **`exists`**   | `{exists=["::pyproject_toml"]}`     | all paths exist                    |
| **`platform`** | `{platform={system=".*Windows.*"}}` | `platform` value (as JSON) matches |

## `doitoml` configuration

| key                | default                | field data type | field description                                                                                      |
| ------------------ | ---------------------- | --------------- | ------------------------------------------------------------------------------------------------------ |
| **`config_paths`** | `[]`                   | list of strings | relative paths to find more `doitoml` config sources: can use the `:get` [DSL] to extract partial data |
| **`fail_quietly`** | `true`                 | `bool`          | try to emit short, helpful errors with context                                                         |
| **`update_env`**   | `true`                 | `bool`          | use the `env` key to update the outer running environment variables                                    |
| **`validate`**     | `true`                 | `bool`          | use `jsonschema` to preflight tasks before `doit`                                                      |
| **`safe_paths`**   | parent of first config | list of strings | paths that are considered "safe" for doitoml to work with.                                             |

[dsl]: ../how-to/dsl.md

<style>
    .bd-container, .bd-container__inner, .bd-content, .bd-article-container, .bd-article, #demo {
        width: 100% !important;
        max-width: unset !important;
        justify-content: stretch;
        flex: 1;
        display: flex;
        flex-direction: column;
    }
    .bd-header-article, .bd-sidebar-secondary, .bd-footer-article, .bd-footer, .bd-sidebar-primary, h1 {
        display: none;
    }
    article > section  {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
    }
    article > section > section {
        max-width: 45em;
        padding-right: 1em;
    }
</style>
