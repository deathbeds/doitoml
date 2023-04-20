# `doitoml`

> Load declarative tasks for [doit] from TOML, JSON, YAML, and other files.

[doit]: https://github.com/pydoit/doit

## Install

> TBD: for now, see the [contributing guide] for a development install.
>
> ```bash
> pip install doitoml
> ```
>
> or
>
> ```bash
> mamba install -c conda-forge doitoml
> ```

[contributing guide]: https://github.com/deathbeds/doitoml/tree/main/CONTRIBUTING.md

## Usage

1. Enable `doitoml`

- in `pyproject.toml`...

```toml
[tool.doit]
loader = "doitoml"
```

- or in a `dodo.py`...

```py
# dodo.py
from doitoml import DoiTOML
d = DoiTOML()
globals().update(d.tasks())
```

2. add `[tool.doitoml]` to your `pyproject.toml`
   - _optionally_, add more sources like `package.json`
   - or nested `pyproject.toml`
3. run `doit`
   - get shippable, reproducible software artifacts
     - and/or docs, test reports, linter findings, or anything else your project builds
4. run `doit` again
   - hopefully **don't do anything**
     - nothing has changed, so there should be nothing to do
5. do your work
   - add new files
   - change existing files
   - remove files
6. run `doit` again
   - only **do what _needs_ to be done**

## The Simplest Example

> The minimum footprint for a `doitoml` project.

The simplest way to use `doitoml` requires only a `pyproject.toml`, which `doit`
will already check for configuration data.

<!-- toml examples/no-dodo -->

```toml
[tool.doit]
loader = "doitoml"
verbosity = 2

[tool.doitoml.tasks.hello]
actions = ['echo "Hello World!"']
```

<!-- toml examples/no-dodo -->

Running:

```bash
doit
```

Will print out:

```bash
.  hello:
Hello World!
```

## A Full Example

> A team is building a Python web application, shipped as a `.whl`. `nodejs` is used for a build step.

While _every_ project is different, we'll assume this team uses some fairly standard
opinions:

<details>

<summary><i>Explore the file tree...</i></summary>

<!-- tree examples/py-js-web -->

```
  README.md
  LICENSE
  pyproject.toml
  dodo.py
  src/
    foo/
      __init__.py
      app.py
  js/
    package.json
    yarn.lock
    tsconfig.json
    webpack.config.js
    src/
      index.ts
    style/
      index.css
```

<!-- tree examples/py-js-web -->

</details>

### `dodo.py`

While it's _yet another file_ in the root of a repo, having a top-level `dodo.py` makes it
easier to tell that `doit` is used, and allows for fine-grained customization not
covered by `doitoml`.

<details>

<summary><i>Explore <code>dodo.py</code>...</i></summary>

<!-- py examples/py-js-web/dodo.py -->

```py
from doitoml import DoiTOML
doitoml = DoiTOML()
globals().update(doitoml.tasks())
```

<!-- py examples/py-js-web/dodo.py -->

</details>

### `pyproject.toml`

Like many modern python tools, `doit` will discover its configuration in the the
well-known file `pyproject.toml`, under the `tool.doit` key.

`tool.doitoml` can further affect this behavior.

<details>

<summary><i>Explore <code>pyproject.toml</code>...</i></summary>

<!-- toml examples/py-js-web/pyproject.toml -->

```toml
[tool.doit]
default_tasks = ["backend:build"]

[tool.doitoml.config]
backend = "./pyproject.toml"
frontend = "./js/package.json"

[tool.doitoml.env]
FOO_PY_VERSION = ":get::toml::./pyproject.toml::project::version"

[tool.doitoml.paths]
whl = ["dist/foo-${FOO_PY_VERSION}-py3-none-any.whl"]
py_src = [":rglob::src::*.py"]
readme = ["README.md"]
license = ["LICENSE"]
ppt = ["pyproject.toml"]

[tool.doitoml.tasks.build]
file_dep = ["::readme", "::license", "::ppt", "::py_src", "::frontend::dist"]
targets = ["::whl"]
actions = [["pyproject-build"]]
```

<!-- toml examples/py-js-web/pyproject.toml -->

</details>

### `package.json`

Based on the `pyproject.toml`, the `js/package.json` will be loaded, and run
tasks inside that folder.

<details>

<summary><i>Explore <code>package.json</code>...</i></summary>

<!-- json examples/py-js-web/js/package.json -->

```json
{
  "name": "foo",
  "scripts": {
    "build:lib": "tsc -b",
    "build:dist": "webpack"
  },
  "doitoml": {
    "paths": {
      "pj": ["package.json"],
      "ts_src": ["rglob:src:*.ts"],
      "ts_cfg": ["tsconfig.json"],
      "ts_buildinfo": ["tsconfig.tsbuildinfo"],
      "y_lock": ["yarn.lock"],
      "y_integrity": ["node_modules/.yarn-integrity"],
      "w_cfg": ["webpack.config.js"],
      "dist_html": ["../src/static/index.html"],
      "style": [":rglob:style:*"]
    },
    "tasks": {
      "install": {
        "file_dep": ["::y_lock", "::pj"],
        "targets": ["::y_integrity"],
        "actions": [["yarn", "--frozen-lockfile"]]
      }
      "build:lib": {
        "file_dep": ["::y_integrity", "::ts_cfg", "::ts_src"],
        "targets": ["::ts_buildinfo"],
        "actions": [["yarn", "build:lib"]]
      },
      "build:dist": {
        "file_dep": ["::y_integrity", "::ts_buildinfo", "::w_cfg", "::style"],
        "targets": ["::dist"],
        "actions": [["yarn", "build:dist"]]
      }
    }
  }
}
```

<!-- json examples/py-js-web/js/package.json -->

</details>

### Build the Wheel

Running `doit` would run, in the following order:

- `cd js`
  - `yarn --frozen-lockfile`
  - `yarn build:lib`
  - `yarn build:dist`
- `cd ..`
  - `python-build`

... leaving an up-to-date `.whl` file in `dist`. **Hooray!**

### Make Changes

Later, after changing, adding, or removing, a `.ts` file, the
`yarn --frozen-lockfile` task would be skipped, but all other tasks would run.

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
