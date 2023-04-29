# Templates

Task _templates_ allow for generating tasks based on _paths_, _command tokens_ and
_environment variables_.

## Use JSON-e for declarative tasks

If [`json-e`](https://pypi.org/project/json-e/) is installed, any configuration source
may define tasks based on a JSON-based structure.

Like string template libraries, JSON-e supports a large number _operators_,
_expressions_, and _built-ins_. Unlike these, it takes as input, operates with, and
returns JSON-like objects.

### `$map`

A common use case is to create a number of tasks, changing only certain key values.

```toml
# pyproject.toml
[tool.doitoml.templates.json-e.tasks.echo]
"$map": ["a", "b"]

[tool.doitoml.templates.json-e.tasks.echo."each(x)"]
name = "${x}"
actions = [{"$eval" = "['echo', x]"}]
```

This would generate two tasks:

```bash
echo:a
echo:b
```

## Use Jinja2 for declarative tasks

If [`jinja2`](https://pypi.org/project/jinja2) is installed, any configuration source
may use `jinja2` to define tasks as a string which will be parsed into JSON-compatible
data.

For example, a `pyproject.toml` with `jinja2` and `pyyaml` installed can declare tasks
with embedded YAML:

```toml
# pyproject.toml
[tool.doitoml.tokens]
greets = ["hello", "howdy"]

[tool.doitoml.templates.jinja2.tasks.greet]
yaml = """
{% for g in tokens[":greets"] %}
- name: {{ g }}
  actions: [[echo, {{ g }}]]
{% endfor %}
"""
```

This would generate two tasks:

```
greet:hello
greet:howdy
```

Alternately, tasks can be declared as an object, omitting `name`:

```toml
# pyproject.toml
[tool.doitoml.tokens]
greets = ["hello", "howdy"]

[tool.doitoml.templates.jinja2.tasks.greet]
yaml = """
{% for g in tokens[":greets"] %}
{{ g }}:
  actions: [[echo, {{ g }}]]
{% endfor %}
"""
```
