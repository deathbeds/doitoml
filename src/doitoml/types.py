"""Types for ``doitoml`` (but mostly ``doit``)."""
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from typing_extensions import TypedDict

Strings = List[str]
Paths = List[Path]
PathOrString = Union[Path, str]
PathOrStrings = List[PathOrString]

MaybeString = Optional[str]
MaybeStrings = Optional[Strings]
MaybePath = Optional[Path]
MaybePaths = Optional[Paths]
MaybePathOrString = Optional[PathOrString]
MaybePathsOrStrings = Optional[PathOrStrings]

Platform = str
Platforms = List[Platform]
MaybePlatforms = Optional[Platforms]

ShellAction = str
Boolish = Union[bool, None]
ShellStringArgsAction = List[str]
ShellArgsAction = List[Union[str, Path]]
FnAction = Callable[[], Boolish]
CallAction = Callable[..., Boolish]
CallArgsAction = Tuple[CallAction, List[Any]]
CallArgsKwargsAction = Tuple[Callable[..., Boolish], List[Any], Dict[str, Any]]
Action = Union[
    ShellAction,
    ShellStringArgsAction,
    ShellArgsAction,
    FnAction,
    CallAction,
    CallArgsAction,
    CallArgsKwargsAction,
]


class Task(TypedDict, total=False):

    """a mostly-inaccurate, but well-intentioned definition of some doit task."""

    # pretty much required
    name: Optional[str]
    actions: List[Action]
    doc: str
    # strongly encouraged
    file_dep: List[Path]
    targets: List[Path]
    # meh
    title: Callable[..., str]
    task_dep: List[str]
    uptodate: List[Callable[[], Boolish]]
    clean: List[Path]
    # seldom
    verbosity: int
    meta: Dict[str, Any]
    # whoa
    getargs: Dict[str, Tuple[str, Any]]
    calc_dep: List[str]
    watch: List[str]


ActionOrTask = Union[Action, Dict[str, Any], Task]

TaskGenerator = Generator[Task, None, None]
TaskOrTaskGenerator = Union[Task, TaskGenerator]
TaskFunction = Callable[[], TaskOrTaskGenerator]


PrefixedTaskGenerator = Generator[Tuple[Tuple[str, ...], Task], None, None]

PrefixedTasks = Dict[Tuple[str, ...], Task]
PrefixedPaths = Dict[Tuple[str, ...], Paths]
PrefixedStrings = Dict[Tuple[str, ...], List[str]]
PrefixedStringsOrPaths = Dict[Tuple[str, ...], List[Union[str, Path]]]
GroupedTasks = Dict[str, PrefixedTasks]


class ConfigDict(TypedDict, total=False):

    """Internal representation of the configuration."""

    env: Dict[str, str]
    paths: PrefixedPaths
    tasks: PrefixedTasks
