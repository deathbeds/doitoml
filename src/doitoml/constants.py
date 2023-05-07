"""Constants for ``doitoml``."""
#: default encoding
from typing import Literal

UTF8 = "utf-8"

#: package/config name
NAME = "doitoml"


class DEFAULTS:

    """``doitoml`` config values."""

    #: shell tokens
    TOKENS: Literal["tokens"] = "tokens"
    #: the fallback config path
    CONFIG_PATH: Literal["./pyproject.toml"] = "./pyproject.toml"
    #: the key for extra sources
    CONFIG_PATHS: Literal["config_paths"] = "config_paths"
    #: the key for extra sources
    UPDATE_ENV: Literal["update_env"] = "update_env"
    #: the key for controlling error verbosity
    FAIL_QUIETLY: Literal["fail_quietly"] = "fail_quietly"
    #: the key for controlling validation
    VALIDATE: Literal["validate"] = "validate"
    #: the values that will be read from the first config file
    ALL_FROM_FIRST_CONFIG = [UPDATE_ENV, FAIL_QUIETLY, VALIDATE, CONFIG_PATH]


class ENTRY_POINTS:

    """``doitoml`` extension points."""

    #: extend the ``doitoml`` DSL
    DSL: Literal["doitoml.dsl.v0"] = "doitoml.dsl.v0"
    #: extend the ``doitoml`` source parser vocabulary
    PARSER: Literal["doitoml.parser.v0"] = "doitoml.parser.v0"
    #: extend the ``doitoml`` config parser vocabulary
    CONFIG: Literal["doitoml.config-parser.v0"] = "doitoml.config-parser.v0"
    #: extend the ``doitoml`` actor vocabulary
    ACTOR: Literal["doitoml.actor.v0"] = "doitoml.actor.v0"
    #: extend the ``doitoml`` templater vocabulary
    TEMPLATER: Literal["doitoml.templater.v0"] = "doitoml.templater.v0"
    #: extend the ``doitoml`` uptodate vocabulary
    UPDATER: Literal["doitoml.updater.v0"] = "doitoml.updater.v0"
    #: extend the ``doitoml`` skip vocabulary
    SKIPPER: Literal["doitoml.skipper.v0"] = "doitoml.skipper.v0"


class DOIT_TASK:

    """A collection of well-known ``doit`` keys."""

    #: ``doit`` actions
    ACTIONS: Literal["actions"] = "actions"
    #: field for arbitrary data in tasks
    META: Literal["meta"] = "meta"
    #: field for task up-to-date checks (might overload `file_dep` and `task_dep`)
    UPTODATE: Literal["uptodate"] = "uptodate"
    #: ``doit`` task items known to be lists
    LIST_KEYS = ["file_dep", "task_dep", "targets", "actions", "clean"]
    #: ``doit`` keys that are always paths
    RELATIVE_LISTS = ["file_dep", "targets", "clean"]


class DOITOML_META:

    """Keys of the ``doitoml`` map in ``doit`` task ``meta``."""

    #: skipping tasks with non-falsey values
    SKIP: Literal["skip"] = "skip"
    #: set the current working directory of a task
    CWD: Literal["cwd"] = "cwd"
    #: environment variables for this task
    ENV: Literal["env"] = "env"
    #: file to capture stdout and stderr
    LOG: Literal["log"] = "log"
    #: the file that defined the task
    SOURCE: Literal["source"] = "source"


#: all the false things
FALSEY = ["", "false", "0", "0.0", "{}", "[]", "null", "none"]

#: fnmatch triggers
FNMATCH_WILDCARDS = "*?["
