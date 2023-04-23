from typing import Any, Dict, List, Literal, TypedDict, Union

from typing_extensions import Required

Action = Union["ShellAction", "TokenAction", "ActorAction"]
"""
action.

oneOf
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
    log: Required[List["_DoitomlMetadataaLogItem"]]
    """ Required property """

    skip: str


class DoitomlSchema(TypedDict, total=False):

    """doitoml Schema.

    schema for ``doitoml`` configuration
    """

    cmd: Required["CommandTokens"]
    """ Required property """

    env: Required["EnvironmentVariables"]
    """ Required property """

    paths: Required["PathTokens"]
    """ Required property """

    tasks: Required[Dict[str, "Task"]]
    """
    named tasks

    Required property
    """


EnvironmentVariables = Dict[str, str]
""" environment variables. """


class Metadata(TypedDict, total=False):

    """Metadata."""

    doitoml: "DoitomlMetadataa"


PathTokens = Dict[str, List[str]]
""" path tokens. """


ShellAction = str
""" shell action. """


class Task(TypedDict, total=False):

    """Task."""

    actions: List["Action"]
    calc_dep: List[str]
    doc: str
    file_dep: List[str]
    meta: "Metadata"
    name: str
    targets: List[str]
    title: str
    verbosity: "_TaskVerbosity"
    watch: List[str]


TokenAction = List[str]
""" token action. """


_DoitomlMetadataaLogItem = Union[str, None]
""" oneOf """


_TaskVerbosity = Union[Literal[1], Literal[2], Literal[3]]
_TASKVERBOSITY_1: Literal[1] = 1
"""The values for the '_TaskVerbosity' enum"""
_TASKVERBOSITY_2: Literal[2] = 2
"""The values for the '_TaskVerbosity' enum"""
_TASKVERBOSITY_3: Literal[3] = 3
"""The values for the '_TaskVerbosity' enum"""
