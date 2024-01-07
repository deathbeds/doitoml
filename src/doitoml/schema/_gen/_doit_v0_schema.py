from typing import Any, Dict, List, Literal, TypedDict, Union

from typing_extensions import Required

Action = Union["ShellAction", "TokenAction", "ActorAction"]
"""
action.

Aggregation type: oneOf
"""


ActorAction = Dict[str, Any]
"""
actor action.

a custom action
"""


CommandTokens = Dict[str, List[str]]
"""
command tokens.

command tokens which may be expanded as paths
"""


class DoitomlMetadata(TypedDict, total=False):

    """doitoml Metadata."""

    cwd: Required[str]

    env: "EnvironmentVariables"

    log: Required[List["_DefinitionsDoitomlLogItem"]]

    skip: Union[str, Union[int, float], None, Dict[str, Any]]

    source: Required[str]
    """ Required property """
    """
    environment variables.

    environment variables shared among all tasks
    """
    """ Required property """
    """ Aggregation type: oneOf """
    """ Required property """


class DoitomlSchema(TypedDict, total=False):

    """doitoml schema.

    schema for ``doitoml`` configuration
    """

    env: Required["EnvironmentVariables"]

    paths: Required["PathTokens"]

    tasks: Required["_DefinitionsTasks"]

    templates: Dict[str, Any]

    tokens: Required["CommandTokens"]
    """
    environment variables.

    environment variables shared among all tasks

    Required property
    """
    """
    path tokens.

    paths to expand and normalize, relative to the current working directory

    Required property
    """
    """
    doit tasks

    Required property
    """
    """ extensible task generators """
    """
    command tokens.

    command tokens which may be expanded as paths

    Required property
    """


EnvironmentVariables = Dict[str, str]
"""
environment variables.

environment variables shared among all tasks
"""


class Metadata(TypedDict, total=False):

    """Metadata."""

    doitoml: "DoitomlMetadata"
    """ doitoml Metadata. """


PathTokens = Dict[str, List["_DefinitionsArrayOfPathsItem"]]
"""
path tokens.

paths to expand and normalize, relative to the current working directory
"""


ShellAction = str
""" shell action. """


class Task(TypedDict, total=False):

    """Task.

    a doit task
    """

    actions: List["Action"]
    calc_dep: List["_DefinitionsArrayOfPathsItem"]
    doc: str
    file_dep: List["_DefinitionsArrayOfPathsItem"]
    meta: "Metadata"

    name: str
    targets: List["_DefinitionsArrayOfPathsItem"]
    title: str
    uptodate: List["Uptodate"]
    verbosity: "_DefinitionsVerbosity"

    watch: List["_DefinitionsArrayOfPathsItem"]
    """ Metadata. """
    """ level of console output to show. 0 shows no output, 1 shows error output, 2 shows all output """


TokenAction = List[str]
""" token action. """


Uptodate = Union[bool, str, Dict[str, Any], None]
"""
uptodate.

Aggregation type: oneOf
"""


_DefinitionsArrayOfPathsItem = str
""" minLength: 1 """


_DefinitionsDoitomlLogItem = Union[str, None]
""" Aggregation type: oneOf """


_DefinitionsTasks = Dict[str, "Task"]
""" doit tasks """


_DefinitionsVerbosity = Union[Literal[0], Literal[1], Literal[2]]
""" level of console output to show. 0 shows no output, 1 shows error output, 2 shows all output """
_DEFINITIONSVERBOSITY_0: Literal[0] = 0
"""The values for the 'level of console output to show. 0 shows no output, 1 shows error output, 2 shows all output' enum"""
_DEFINITIONSVERBOSITY_1: Literal[1] = 1
"""The values for the 'level of console output to show. 0 shows no output, 1 shows error output, 2 shows all output' enum"""
_DEFINITIONSVERBOSITY_2: Literal[2] = 2
"""The values for the 'level of console output to show. 0 shows no output, 1 shows error output, 2 shows all output' enum"""
