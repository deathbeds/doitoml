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

#: non-standard. for skipping tasks with non-falsey values
DOITOML_TASK_SKIP = "_skip"
#: non-standard. for setting the current working directory of a task
DOITOML_TASK_CWD = "_cwd"
#: all the false things
FALSEY = ["", "false", "0", "0.0", "{}", "[]", "null", "none"]

## entry points
#: extend the ``doitoml`` DSL
ENTRY_POINT_DSL = "doitoml.dsl.v0"
#: extend the ``doitoml`` source parser vocabulary
ENTRY_POINT_PARSER = "doitoml.parser.v0"
#: extend the ``doitoml`` config parser vocabulary
ENTRY_POINT_CONFIG = "doitoml.config-parser.v0"
#: extend the ``doitoml`` actor vocabulary
ENTRY_POINT_ACTOR = "doitoml.actor.v0"
#: extend the ``doitoml`` templater vocabulary
ENTRY_POINT_TEMPLATER = "doitoml.templater.v0"

## doit constants
#: ``doit`` actions
DOIT_ACTIONS = "actions"
#: ``doit`` task items known to be lists
DOIT_TASK_LIST_KEYS = ["file_dep", "task_dep", "targets", "actions", "clean"]
#: ``doit`` keys that are always paths
DOIT_PATH_RELATIVE_LISTS = ["file_dep", "targets", "clean"]
