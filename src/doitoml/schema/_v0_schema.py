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
""" command tokens. """


class DoitomlMetadataa(TypedDict, total=False):

    """doitoml Metadataa."""

    cwd: Required[str]
    """ Required property """

    env: "EnvironmentVariables"
    """ environment variables. """

    log: Required[List["_DoitomlMetadataaLogItem"]]
    """ Required property """

    skip: Union[str, Union[int, float], None, Dict[str, Any]]
    """ Aggregation type: oneOf """

    source: Required[str]
    """ Required property """


class DoitomlSchema(TypedDict, total=False):

    """doitoml Schema.

    schema for ``doitoml`` configuration
    """

    env: Required["EnvironmentVariables"]
    """
    environment variables.

    Required property
    """

    paths: Required["PathTokens"]
    """
    path tokens.

    Required property
    """

    tasks: Required[Dict[str, "Task"]]
    """ Required property """

    tokens: Required["CommandTokens"]
    """
    command tokens.

    Required property
    """


EnvironmentVariables = Dict[str, str]
""" environment variables. """


class Metadata(TypedDict, total=False):

    """Metadata."""

    doitoml: "DoitomlMetadataa"
    """ doitoml Metadataa. """


PathTokens = Dict[str, List["_ArrayOfPathsItem"]]
""" path tokens. """


ShellAction = str
""" shell action. """


class Task(TypedDict, total=False):

    """Task."""

    actions: List["Action"]
    calc_dep: List["_ArrayOfPathsItem"]
    doc: str
    file_dep: List["_ArrayOfPathsItem"]
    meta: "Metadata"
    """ Metadata. """

    name: str
    targets: List["_ArrayOfPathsItem"]
    title: str
    uptodate: List["Uptodate"]
    verbosity: "_TaskVerbosity"
    watch: List["_ArrayOfPathsItem"]


TokenAction = List[str]
""" token action. """


Uptodate = Union[bool, str, Dict[str, Any], None]
"""
uptodate.

Aggregation type: oneOf
"""


_ArrayOfPathsItem = str
""" minLength: 1 """


_DoitomlMetadataaLogItem = Union[str, None]
""" Aggregation type: oneOf """


_TaskVerbosity = Union[Literal[1], Literal[2], Literal[3]]
_TASKVERBOSITY_1: Literal[1] = 1
"""The values for the '_TaskVerbosity' enum"""
_TASKVERBOSITY_2: Literal[2] = 2
"""The values for the '_TaskVerbosity' enum"""
_TASKVERBOSITY_3: Literal[3] = 3
"""The values for the '_TaskVerbosity' enum"""
