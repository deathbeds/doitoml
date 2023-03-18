"""Opinionated, declarative ``doit`` tasks from TOML, JSON, and more."""
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import doit.action
import doit.tools

from .config import Config
from .constants import ACTIONS, DEFAULT_CONFIG_PATH
from .entry_points import EntryPoints
from .errors import DoitomlError, EnvVarError, TaskError
from .types import (
    GroupedTasks,
    PathOrStrings,
    PrefixedTasks,
    Task,
    TaskFunction,
    TaskGenerator,
)

MaybeLogLevel = Optional[Union[str, int]]


class DoiTOML:

    """An opinionated pyproject.toml-based doit task generator."""

    fail_quietly: bool = False
    config: Config
    log: logging.Logger
    entry_points: EntryPoints

    def __init__(
        self,
        config_paths: Optional[PathOrStrings] = None,
        *,
        update_env: Optional[bool] = None,
        fail_quietly: Optional[bool] = None,
        log: Optional[logging.Logger] = None,
        log_level: MaybeLogLevel = None,
    ) -> None:
        """Initialize a ``doitoml`` task generator."""
        self.fail_quietly = False if fail_quietly is None else fail_quietly

        try:
            self.log = self.init_log(log, log_level)
            self.entry_points = EntryPoints(self)
            self.config = self.init_config(config_paths or [])
            # initialize late for ``entry_points`` that reference ``self.entry_points``
            self.entry_points.initialize()
            self.config.initialize()
            if update_env:
                self.update_env()
        except DoitomlError as err:
            if self.fail_quietly:
                self.log.error(err)
                sys.exit(1)
            else:
                raise err

    def init_log(
        self,
        log: Optional[logging.Logger] = None,
        log_level: MaybeLogLevel = None,
    ) -> logging.Logger:
        """Initialize logging."""
        log = log or logging.getLogger()
        if log_level:
            log.setLevel(log_level)
        return log

    def init_config(self, config_paths: PathOrStrings) -> Config:
        """Initialize configuration."""
        paths = [Path(path).resolve() for path in config_paths or [DEFAULT_CONFIG_PATH]]
        return Config(self, paths)

    def tasks(self) -> Dict[str, TaskFunction]:
        """Generate functions compatible with the default ``doit`` loader style."""
        tasks = {}

        task_groups = self.group_tasks(self.config.tasks)
        for task_name, subtasks in task_groups.items():
            if not task_name:
                subgroup = self.group_tasks(subtasks)
                for subtask_name, sub2_tasks in subgroup.items():
                    task = self.build_task_group(subtask_name, sub2_tasks)
                    tasks[task.__name__] = task
            else:
                task = self.build_task_group(task_name, subtasks)
                tasks[task.__name__] = task

        return tasks

    def group_tasks(self, tasks: PrefixedTasks) -> GroupedTasks:
        """Group tasks by their first prefix."""
        groups: GroupedTasks = {}
        for prefixes, task in tasks.items():
            groups.setdefault(prefixes[0], {}).update({prefixes[1:]: task})
        return groups

    def get_env(self, key: str, default: Optional[str] = None) -> str:
        """Get an environment variable from the real (or in-progress) environment."""
        value = os.environ.get(key, self.config.env.get(key))
        if value is None:
            if default is not None:
                return default
            message = f"{key} was not found in any environment, no default given"
            raise EnvVarError(message)
        return value

    def update_env(self) -> None:
        """Update environment variables."""
        os.environ.update(self.config.env)

    def build_task_group(
        self,
        prefix: str,
        subtasks: PrefixedTasks,
    ) -> TaskFunction:
        """Build a nested ``doit`` task group."""

        def task() -> TaskGenerator:
            for subtask_name, subtask in subtasks.items():
                if ACTIONS in subtask:
                    yield self.build_subtask(subtask_name, subtask)
                else:
                    message = f"Unepxected subtasks {prefix} {subtask}"
                    raise DoitomlError(message)

        task.__name__ = f"task_{prefix}"
        task.__doc__ = f"... {len(subtasks)} {prefix} tasks"
        return task

    def build_subtask(self, task_name: Tuple[str, ...], raw_task: Task) -> Task:
        """Build a single generated ``doit`` task."""
        task: Task = {"name": ":".join(task_name)}
        task.update(raw_task)
        cwd = task.pop("cwd", None)  # type: ignore
        new_actions: List[Any] = []
        if cwd:
            new_actions += [(doit.tools.create_folder, [cwd])]
            for i, action in enumerate(task["actions"]):
                if not isinstance(action, (str, list)):
                    message = f"Cannot run task {task_name} action {i} in {cwd}"
                    raise TaskError(message)
                new_actions += [
                    doit.tools.CmdAction(
                        action,
                        cwd=str(cwd),
                        shell=False,
                    ),
                ]

            task["actions"] = new_actions
        return cast(Task, task)
