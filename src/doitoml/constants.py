"""Constants for ``doitoml``."""
#: default encoding
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
    DSL = "doitoml.dsl.v0"
    #: extend the ``doitoml`` source parser vocabulary
    PARSER = "doitoml.parser.v0"
    #: extend the ``doitoml`` config parser vocabulary
    CONFIG = "doitoml.config-parser.v0"
    #: extend the ``doitoml`` actor vocabulary
    ACTOR = "doitoml.actor.v0"
    #: extend the ``doitoml`` templater vocabulary
    TEMPLATER = "doitoml.templater.v0"


class DOIT_TASK:

    """A collection of well-known ``doit`` keys."""

    #: ``doit`` actions
    ACTIONS = "actions"
    #: ``doit`` task items known to be lists
    LIST_KEYS = ["file_dep", "task_dep", "targets", "actions", "clean"]
    #: ``doit`` keys that are always paths
    RELATIVE_LISTS = ["file_dep", "targets", "clean"]
    #: field for arbitrary data in tasks
    META = "meta"


class DOITOML_META:

    """Keys of the ``doitoml`` map in ``doit`` task ``meta``."""

    #: skipping tasks with non-falsey values
    SKIP = "skip"
    #: set the current working directory of a task
    CWD = "cwd"
    #: environment variables for this task
    ENV = "env"
    #: file to capture stdout
    STDOUT = "stdout"
    #: file to capture stderr
    STDERR = "stderr"


#: all the false things
FALSEY = ["", "false", "0", "0.0", "{}", "[]", "null", "none"]
