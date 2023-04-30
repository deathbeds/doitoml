# `doit` Good

Here are some opinions on writing portable, robust `doit` workflows.

## Pick good `default_tasks`

A practical convention is that running `doit`, without any inputs, should leave the
project in a _useful_ state for development and inspection.

For example, a good default to consider is what one might show on
[MyBinder](https://mybinder.org), with the simplest possible `postBuild` file like:

```bash
#!/usr/bin/env bash
doit
```

This should leave a project with:

- a verified, up-to-date installed runtime and test dependencies
- any packages-under-development installed

## Get responsive and stable

A good `doit` task tree should be _responsive_ and _stable_.

A _responsive_ task tree should correctly run all of the tasks in the right order,
leaving the correct files on disk. When an important file (or part of it) changes, the
right tasks and outputs should be out-of-date.

A _stable_ task tree should ideally only require one command, and running the same task
without changing any files, should not do any extra work.

## Format all the things

A key way to get the most _stable_ product is to make liberal use of automated
formatters, with as aggressive-as-possible options. A `doit format` task that automates
as much as possible will not only improve the _stability_ and _responsiveness_ of a
`doit` task tree, but also lead to cleaner revision control history.

For example, on `doitoml`'s own Python code, `ssort`, `black`, and `ruff` are all used
to take as much guesswork as possible out of line- and token-level syntax choices.

## Single sources of truth

Any time there is a _magic number_ (or other value) that is important to multiple
processes, try to store it in exactly one place, and either reuse it from there, or
check other files against it.

```{hint}
For example, in a Python project, storing the package's version in _exactly_ `pyproject.toml#/project/version` and nowhere else ensures that no automation or build
scripts go stale.
```

## Use `file_dep` and `targets`

While `task_dep` and `uptodate` can be useful in a pinch, hash-based comparisons of
well-known files save time and effort.

```{hint}
Using [custom logging](../how-to/logging.md) is a good way to get predictablly-named
file outputs from otherwise hard-to-observe tasks.
```

One of the key benefits of knowing this dependency tree up-front is being able to use
`doit --process=2` (or `-n2`). This utilizes modern, multi-core systems without too much
coordination or needless re-work due to long, but avoidable, command errors about
missing files, or worse, incorrect build ordering based on stale data.

## Avoid configurable task options

`doit` allows tasks to declare their own options which are propagated to the CLI, and
discoverable with `doit help {task-name}`. However, these don't compose very well
without very careful management of names.

```{hint}
A useful convention is to make use of environment variables, which are more
conventionally configurable, to set options to specific tasks. Combining these with
`skip` metadata provided by `doitoml` allows for customizing tasks when being run
in different contexts.
```
