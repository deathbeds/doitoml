# Contributing

## Prerequisites

### Checkout

- `git`
  ```bash
  git clone https://github.com/deathbeds/doitoml
  cd doitoml
  ```

### Setup with `mamba` (recommended)

- [mambaforge](https://conda-forge.org/miniforge/)

  ```bash
  mamba env update --file .binder/environment.yml --prefix .venv
  source activate ./.venv  # just `activate` on windows
  ```

### Setup with `pip`

- use whatever tool you prefer for virtualenvs

  ```bash
  python -m pip install -e .[dev]
  ```

## `doit`

Everything else is handled by `doit`.

### Basically do everything

```bash
doit
```

### See all the tasks

```bash
doit list
```

### Learn more about a task

```bash
doit info [task name]
```
