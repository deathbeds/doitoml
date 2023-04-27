# Extending

The `doitoml` data model can be extended in a number of places, either by using
existing extensible entry points or installing additional packages or creating your
own reusable utility packages.

## Simple Python extensions

### `py` action

The `py` action provides a way to use arbitrary importable python names for actions, using
the `entry_point` notation of `module.submodule:function`. Many Python `stdlib` functions
that accept simple, JSON-compatible values work out of the box.

```toml
[tool.doitoml.tasks.copy]
actions = [
    { py = "shutil:copytree", kwargs = { src = "from/path/", dst = "to/path" } }
]
```

The imported function must return `None` or `True` on _success_. A return value of `False`,
or any raised `Exception`, is considered a _failure_, and any other return value is
an _error_.

## Building new extensions

See the [API](./api.md) for more information: most existing functionality is implemented
as modular components, including DSL extensions, config sources, custom actions, and more.
