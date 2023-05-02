# `doitoml`

> Load declarative tasks for [doit] from TOML, JSON, YAML, and other files.

|            docs             |                                          install                                           |                build                 |
| :-------------------------: | :----------------------------------------------------------------------------------------: | :----------------------------------: |
| [![docs][docs-badge]][docs] | [![install from pypi][pypi-badge]][pypi] [![install from conda-forge][conda-badge]][conda] | [![build][workflow-badge]][workflow] |

> See the [full documentation][docs] for more information.

## Install

|         `pip`         |   `conda` (or `mamba`, `micromamba`)   |
| :-------------------: | :------------------------------------: |
| `pip install doitoml` | `conda install -c conda-forge doitoml` |

## Features

- **declarative** automation in a **single** `pyproject.toml`, or...
  - other well-known configuration paths like `package.json`
  - any number of namespaced TOML, JSON, [YAML](#extras) files
    - from any key inside them
  - augment and simplify existing `dodo.py` workflows
- reuse and transform **paths** and shell tokens
  - use **globs** and transforms to capture relationships between transformed files
- flexibly configure **environment** variables
- user-defined Python-based **actions** and **up-to-date** checkers
- control the **working directory** and **log paths** of processes and actions
- use [**templates**](#extras) like Jinja2 and JSON-e for advanced use cases
- **extensibility** in any part of the task definition process
  - all core functionality implemented as `entry_point`-based **plugins**

### Extras

These features require additional `pip` or `conda` packages

|                 `pip` | `conda`                   | feature                        |
| --------------------: | ------------------------- | ------------------------------ |
|        `doitoml[all]` | `doitoml-with-all`        | all optional features          |
|     `doitoml[jinja2]` | `doitoml-with-jinja2`     | Jinja2 task templates          |
|     `doitoml[json-e]` | `doitoml-with-json-e`     | JSON-e task templates          |
| `doitoml[jsonschema]` | `doitoml-with-jsonschema` | extra configuration validation |
|       `doitoml[yaml]` | `doitoml-with-yaml`       | YAML-based task sources        |

## Usage

`doitoml` provides no additional command line abilities, and is meant to drop in to the
existing [`doit run`](https://pydoit.org/cmd-run.html) CLI and
[other commands](https://pydoit.org/cmd-other.html).

### A Simple Example

> **Note**
>
> The `doitoml` [GitHub] repository has many examples of different configurations,
> including the project's own `pyproject.toml` and `package.json`.
>
> The [full documentation][docs] includes more information about building concise,
> declarative, reproducible tasks for your project.

The simplest way to use `doitoml` needs only a `pyproject.toml`, which `doit` will
already check for configuration data.

```toml
# pyproject.toml
[project.optional-dependencies]
dev = ["doitoml"]

[tool.doit]
loader = "doitoml"
verbosity = 2

[tool.doitoml.tasks.hello]
actions = ['echo "Hello World!"']
```

After installing the `dev` extra dependency...

```bash
pip install -e .[dev]
```

... and running ...

```bash
doit
```

... you would see ...

```bash
.  hello:
Hello World!
```

## Alternatives

If you don't like `doitoml`, or `doit`, or even Python, no worries! But **please**
consider trying one of these lovely alternatives before giving up and making your team
do everything _The Hard Way_:

- [`doit`][doit]
- [`go-task`](https://github.com/go-task/task)
- [`just`](https://github.com/casey/just)
- [`make`](https://www.gnu.org/software/make)
- [`nx`](https://nx.dev)

## Free Software

`doitoml` is licensed under the [BSD-3-Clause] License.

[bsd-3-clause]: https://github.com/deathbeds/doitoml/tree/main/LICENSE.txt
[contributing guide]: https://github.com/deathbeds/doitoml/tree/main/CONTRIBUTING.md
[docs]: https://doitoml.rtfd.io
[doit]: https://github.com/pydoit/doit
[github]: https://github.com/deathbeds/doitoml
[docs-badge]: https://readthedocs.org/projects/doitoml/badge/?version=latest
[conda-badge]: https://img.shields.io/conda/vn/conda-forge/doitoml
[conda]: https://anaconda.org/conda-forge/doitoml
[pypi-badge]: https://img.shields.io/pypi/v/doitoml
[pypi]: https://pypi.org/project/doitoml
[workflow-badge]:
  https://github.com/deathbeds/doitoml/actions/workflows/ci.yml/badge.svg?branch=main
[workflow]:
  https://github.com/deathbeds/doitoml/actions/workflows/ci.yml?query=branch%3Amain
