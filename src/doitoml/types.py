"""Types for ``doitoml`` (but mostly ``doit``)."""
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union

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


class DoitomlTaskMetadata(TypedDict, total=False):

    """Custom metadata for ``doitoml``."""

    skip: Any
    cwd: PathOrString


class TaskMetadata(TypedDict, total=False):

    """Well-known values in task metadata."""

    doitoml: DoitomlTaskMetadata


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
    uptodate: List[
        Union[bool, None, str, Tuple[Callable[[], Boolish]], Callable[[], Boolish]]
    ]
    clean: List[Path]
    # seldom
    verbosity: int
    meta: TaskMetadata
    # whoa
    getargs: Dict[str, Tuple[str, Any]]
    calc_dep: List[str]
    watch: List[str]


class TemplateSet(TypedDict, total=False):

    """templateable things."""

    tasks: Dict[str, Any]


ActionOrTask = Union[Action, Dict[str, Any], Task]

TaskGenerator = Generator[Task, None, None]
TaskOrTaskGenerator = Union[Task, TaskGenerator]
TaskFunction = Callable[[], TaskOrTaskGenerator]

PrefixedTaskGenerator = Generator[Tuple[Tuple[str, ...], Task], None, None]


PrefixedTasks = Dict[Tuple[str, ...], Task]
PrefixedPaths = Dict[Tuple[str, ...], Paths]
PrefixedTemplates = Dict[str, Dict[str, TemplateSet]]
PrefixedStrings = Dict[Tuple[str, ...], List[str]]
PrefixedStringsOrPaths = Dict[Tuple[str, ...], List[Union[str, Path]]]
GroupedTasks = Dict[str, PrefixedTasks]
LogPaths = Tuple[MaybePath, MaybePath]


class ExecutionContext(NamedTuple):

    """A collection of data relevant to starting a process or calling a function."""

    cwd: Path
    env: Dict[str, str]
    log_paths: LogPaths
    log_mode: str
