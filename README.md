# `doitoml`

> Load declarative tasks for [doit] from TOML, JSON, YAML, and other files.

[doit]: https://github.com/pydoit/doit

## Install

> TBD: for now, see the [contributing guide] for a development install.
> | `pip` | `conda` (or `mamba`, `micromamba`) |
> |:-:|:-:|
> | `pip install doitoml` | `conda install -c conda-forge doitoml`

[contributing guide]: https://github.com/deathbeds/doitoml/tree/main/CONTRIBUTING.md

## Usage

### A Simple Example

The simplest way to use `doitoml` needs only a `pyproject.toml`, which `doit[toml]`
will already check for configuration data.

```toml
# pyproject.toml
[tool.doit]
loader = "doitoml"
verbosity = 2

[tool.doitoml.tasks.hello]
actions = ['echo "Hello World!"']
```

Running:

```bash
doit
```

Will print out:

```bash
.  hello:
Hello World!
```

See the [full documentation][docs] for more information about building concise,
declarative, reproducible tasks for your project.

## Alternatives

If you don't like `doitoml`, or `doit`, or even Python, no worries! But **please**
consider trying one of these lovely alternatives before giving up and making
your team do everything _The Hard Way_:

- [`doit`][doit]
- [`go-task`](https://github.com/go-task/task)
- [`just`](https://github.com/casey/just)
- [`make`](https://www.gnu.org/software/make)
- [`nx`](https://nx.dev)

## Free Software

`doitoml` is licensed under the [BSD-3-Clause] License.

[bsd-3-clause]: https://github.com/deathbeds/doitoml/tree/main/LICENSE.txt
[docs]: https://doitoml.rtfd.io
