"""Constants for ``doitoml``."""
#: default encoding
from typing import Literal

UTF8 = "utf-8"

#: package/config name
NAME = "doitoml"


class DEFAULTS:

    """``doitoml`` config values."""

    #: the fallback config path
    CONFIG_PATH = "./pyproject.toml"
    #: the key for extra sources
    CONFIG_PATHS = "config_paths"
    #: the key for extra sources
    UPDATE_ENV = "update_env"
    #: the key for controlling error verbosity
    FAIL_QUIETLY = "fail_quietly"


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


class DOIT_TASK:

    """A collection of well-known ``doit`` keys."""

    #: ``doit`` actions
    ACTIONS: Literal["actions"] = "actions"
    #: ``doit`` task items known to be lists
    LIST_KEYS = ["file_dep", "task_dep", "targets", "actions", "clean"]
    #: ``doit`` keys that are always paths
    RELATIVE_LISTS = ["file_dep", "targets", "clean"]
    #: field for arbitrary data in tasks
    META: Literal["meta"] = "meta"


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


#: all the false things
FALSEY = ["", "false", "0", "0.0", "{}", "[]", "null", "none"]
