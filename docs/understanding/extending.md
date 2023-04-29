# Extending

The `doitoml` data model can be extended in a number of places, either by:

- using existing extensible features with
  [custom Python functions](../how-to/user-python.md)
- creating reusable utility packages
- installing additional packages that define new DSL, parsers, etc.

## Building new extensions

See the [API](../reference/api.md) for more information: most existing functionality is
implemented as modular components, including DSL extensions, config sources, custom
actions, and more.

### Advertising an extension

Python's `entry_points` feature allows for installed third-party packages to register
new features based on well-known strings.

<details>

<summary>
  For example, here are the core plugins that define <code>doitoml</code>'s behavior.
</summary>

```toml
[project.entry-points."doitoml.actor.v0"]
py = "doitoml.actors.py:PyActor"
[project.entry-points."doitoml.config-parser.v0"]
doitoml-package-json = "doitoml.sources.json.package:PackageJsonParser"
doitoml-pyproject-toml = "doitoml.sources.toml.pyproject:PyprojectTomlParser"
[project.entry-points."doitoml.dsl.v0"]
doitoml-colon-colon-path = "doitoml.dsl:PathRef"
doitoml-colon-get = "doitoml.dsl:Getter"
doitoml-colon-glob = "doitoml.dsl:Globber"
doitoml-dollar-env = "doitoml.dsl:EnvReplacer"
[project.entry-points."doitoml.parser.v0"]
json = "doitoml.sources.json._json:JsonParser"
toml = "doitoml.sources.toml._toml:TomlParser"
yaml = "doitoml.sources.yaml._yaml:YamlParser"
[project.entry-points."doitoml.templater.v0"]
json-e = "doitoml.templaters.jsone:JsonE"
jinja2 = "doitoml.templaters.jinja2:Jinja2"
[project.entry-points."doitoml.updater.v0"]
config_changed = "doitoml.updaters.doit_tools:ConfigChanged"
run_once = "doitoml.updaters.doit_tools:RunOnce"
py = "doitoml.updaters.py:PyUpdater"
```

</details>

#### `entry_point` rank

All entry points may offer a `rank` (default of `100`) that controls the order they will
be checked. This allows third-party extensions to overload some of the built-in
behaviors, by ensuring they run first.

Ties are resolved by the `entry_point` name.
