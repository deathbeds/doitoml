"""Constants for ``doitoml``."""
#: default encoding
UTF8 = "utf-8"

#: package/config name
NAME = "doitoml"

## ``doitoml`` config values
#: the fallback config path
DEFAULT_CONFIG_PATH = "./pyproject.toml"
#: the key for extra sources
DOITOML_CONFIG_PATHS = "config_paths"
#: the key for extra sources
DOITOML_UPDATE_ENV = "update_env"
#: the key for controlling error verbosity
DOITOML_FAIL_QUIETLY = "fail_quietly"

## entry points
#: extend the pydoit DSL
ENTRY_POINT_DSL = "doitoml.dsl.v0"
#: extend the pydoit parser list
ENTRY_POINT_PARSER = "doitoml.parser.v0"
#: extend the pydoit config parser list
ENTRY_POINT_CONFIG = "doitoml.config-parser.v0"
#: extend the pydoit dict action vocabulary
ENTRY_POINT_ACTOR = "doitoml.actor.v0"
#: extend the templater vocabulary
ENTRY_POINT_TEMPLATER = "doitoml.templater.v0"

## doit constants
#: ``doit`` actions
DOIT_ACTIONS = "actions"
#: ``doit`` task items known to be lists
DOIT_TASK_LIST_KEYS = ["file_dep", "task_dep", "targets", "actions", "clean"]
#: ``doit`` keys that are always paths
DOIT_PATH_RELATIVE_LISTS = ["file_dep", "targets", "clean"]

FALSEY = ["", "false", "0", "0.0", "{}", "[]", "null", "none"]
