# Changelog

## 0.2.1 (unreleased)

- [#15] normalizes path drive letters on windows

[#15]: https://github.com/deathbeds/doitoml/issues/15

## 0.2.0

### Data Model

- expands `skip` to allow custom skippers like `any`, `all`, `not`, `exists`, `platform`

### Docs

- adds interactive demo and playground, powered by JupyterLite

### API

- adds `safe_paths` to the Python API
  - arbitrary paths in _shell_ actions are uncheckable, however

### Packaging

- adds `doitoml[test]`

## 0.1.1

### Bugs

- fixes `jsonschema` dependency

### Packaging

- adds `doitoml[all]`

## 0.1.0

- initial release
