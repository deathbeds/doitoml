"""Constants for ``doitoml``."""
#: package/config name
NAME = "doitoml"

#: ``doit`` task items known to be lists
DOIT_TASK_LIST_KEYS = ["file_dep", "task_dep", "targets", "actions"]
ACTIONS = "actions"

UTF8 = "utf-8"

DEFAULT_CONFIG_PATH = "./pyproject.toml"

ENTRY_POINT_DSL = "doitoml.dsl.v0"
ENTRY_POINT_PARSER = "doitoml.parser.v0"
ENTRY_POINT_CONFIG = "doitoml.config-parser.v0"
