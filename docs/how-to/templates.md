# Templates

Task _templates_ allow for generating tasks based on _paths_, _command tokens_ and
_environment variables_.

## JSON-e

If [`json-e`](https://pypi.org/project/json-e/) is installed, a `pyproject.toml` may
define templated tasks.

Like string template libraries, JSON-e supports a large number _operators_,
_expressions_, and _built-ins_. Unlike these, it both takes, operates with, and returns
JSON-like objects.

### `$map`

A common use case is to create a number of tasks, changing only certain key values.

```toml
[tool.doitoml.templates.json-e.tasks.echo]
"$map": ["a", "b"]

[tool.doitoml.templates.json-e.tasks.echo."each(x)"]
name = "${x}"
actions = [
    { "$eval" = "['echo', x]" }
]
```

This would generate two tasks:

```
echo:a
echo:b
```
