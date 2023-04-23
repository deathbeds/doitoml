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

    skip: str
    cwd: str
    log: List["_DoitomlMetadataaLogItem"]


class DoitomlSchema(TypedDict, total=False):

    """doitoml Schema.

    schema for ``doitoml`` configuration
    """

    tasks: Required[Dict[str, "Task"]]
    """
    named tasks

    Required property
    """

    cmd: Required["CommandTokens"]
    """ Required property """

    env: Required["EnvironmentVariables"]
    """ Required property """

    paths: Required["PathTokens"]
    """ Required property """


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

    name: str
    doc: str
    title: str
    actions: List["Action"]
    file_dep: List[str]
    targets: List[str]
    verbosity: "_TaskVerbosity"
    meta: "Metadata"
    calc_dep: List[str]
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
