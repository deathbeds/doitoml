# DSL

## `${}` Get Environment Variables

> Get the value of an environment variable. Usually executed before any other parsers.

<div class="jp-Mermaid">

```{mermaid}
flowchart LR

any-before --> dollar-leftbrace --> var-name --> rightbrace --> any-after

any-before([<i>any text</i>])
dollar-leftbrace(["<code>${</code>"])
rightbrace(["<code>}</code>"])
var-name([<i>a variable name</i>])
any-after([<i>any text</i>])
```

</div>

Environment variables are shared across all `doitoml` configuration files.

### Examples

> TODO

## `:get` Get File Data

> Read a piece of data from a path in a structured file: the result is usally cast to a JSON string, if neccessary.

<div class="jp-Mermaid">

```{mermaid}
flowchart LR

get --> parsers --> paths --> selectors

get([<code>:get</code>])

subgraph parsers [1 parser]
  json([<code>::json</code>])
  toml([<code>::toml</code>])
end

subgraph paths [1 path]
  path([<code>::</code><i>path</i>])
end

subgraph selectors [1+ selectors]
  selector([<code>::</code><i>string or int</i>])
end
```

</div>

Use this to get data from a predictable location in a structured data file, such as a software package version.

### Examples

````{tab-set}

```{tab-item} pyproject.toml

Get a version number.

~~~toml
[project]
version = "0.1.0"

[tool.doitoml.env]
PY_VERSION = ":get::toml::pyproject.toml::project::version"
~~~
```

```{tab-item} package.json

Get a version number.

~~~json
{
  "version": "0.1.0",
  "doitoml": {
    "env": {
      "JS_VERSION": ":get::json::package.json::version"
    }
  }
}
~~~
```

````

## `::` Reference a path or token

> Get the value of any `paths` or `tokens`, either in the same `doitoml` configuration file, or with a named prefix.

<div class="jp-Mermaid">

```{mermaid}
flowchart LR

colon-colon --> namespaces --> token
token -.-> path & tokens

namespace -.-> prefix

colon-colon([<code>::</code>])
token([<code>::</code><i>token or path</i>])

subgraph namespaces [0 or 1 namespace]
  namespace([<code>::</code><i>namespace</i>])
end

subgraph doitoml
  prefix("<code>prefix = ...</code>")
  subgraph paths
    path("<code>some_path = [...]</code>")
  end
  subgraph tokens [tokens]
    tokens("<code>some_cmd = [...]</code>")
  end
end
```

</div>

### Examples

> TODO

## `:glob` Find files

<div class="jp-Mermaid">

```{mermaid}
flowchart LR

glob & rglob --> roots --> matches --> excludes --> subs

glob([<code>:glob</code>])
rglob([<code>:rglob</code>])

subgraph roots [1 root]
  root([<code>::</code><i>path/to/root</i>])
end

subgraph matches [1+ matches]
  match([<code>::</code><i>path/with/*</i>])
end

subgraph excludes [0+ excludes]
  exclude([<code>::!</code>a regex])
end

subgraph subs [0+ substitutions]
  sub([<code>::/s/</code>])
  sub-find([<code>::</code><i>a regex</i>])
  sub-replace([<code>::</code><i>replacement</i>])
  sub --> sub-find --> sub-replace
end
```

</div>

### Examples

> TODO
