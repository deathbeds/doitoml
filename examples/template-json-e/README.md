# template-json-e

This example shows how JSON-e can be used to data-driven tasks.

- for each Python packages discovered by the presence of a `pyproject.toml`
    - a task is created for each package to build `.whl` and `.tar.gz` outputs
    - a hashfile is built of each of the outputs
