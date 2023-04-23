from typing import Any, Dict, List, Literal, TypedDict, Union

from typing_extensions import Required


class DoitomlSchema(TypedDict, total=False):

    """doitoml Schema.

    schema for ``doitoml`` configuration
    """

    tasks: Required[Dict[str, "_Task"]]
    """
    named tasks

    Required property
    """

    cmd: Required[Dict[str, List[str]]]
    """
    named command tokens

    Required property
    """

    env: Required[Dict[str, str]]
    """
    environment variables

    Required property
    """

    paths: Required[Dict[str, List[str]]]
    """
    named paths

    Required property
    """


_Action = Union[str, List[str], "_ActionActor"]
""" oneOf """


_ActionActor = Dict[str, Any]
""" a custom action """


class _Meta(TypedDict, total=False):
    doitoml: "_MetaDoitoml"


class _MetaDoitoml(TypedDict, total=False):
    skip: str
    cwd: str


class _Task(TypedDict, total=False):
    name: str
    doc: str
    title: str
    actions: List["_Action"]
    file_dep: List[str]
    targets: List[str]
    verbosity: "_TaskVerbosity"
    meta: "_Meta"


_TaskVerbosity = Union[Literal[1], Literal[2], Literal[3]]
_TASKVERBOSITY_1: Literal[1] = 1
"""The values for the '_TaskVerbosity' enum"""
_TASKVERBOSITY_2: Literal[2] = 2
"""The values for the '_TaskVerbosity' enum"""
_TASKVERBOSITY_3: Literal[3] = 3
"""The values for the '_TaskVerbosity' enum"""
