"""Opinionated, declarative ``doit`` tasks from TOML, JSON, YAML, and more."""
import logging
import os
import subprocess
import sys
from io import BufferedWriter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import doit.action
import doit.tools

from .config import Config
from .constants import DOIT_TASK, DOITOML_META, NAME
from .entry_points import EntryPoints
from .errors import DoitomlError, EnvVarError, TaskError
from .types import (
    Action,
    GroupedTasks,
    LogPaths,
    PathOrStrings,
    PrefixedTasks,
    Task,
    TaskFunction,
    TaskGenerator,
)

MaybeLogLevel = Optional[Union[str, int]]


class DoiTOML:

    """An opinionated pyproject.toml-based doit task generator."""

    config: Config
    log: logging.Logger
    entry_points: EntryPoints
    cwd: Path

    def __init__(
        self,
        config_paths: Optional[PathOrStrings] = None,
        *,
        cwd: Optional[Path] = None,
        update_env: Optional[bool] = None,
        fail_quietly: Optional[bool] = None,
        log: Optional[logging.Logger] = None,
        log_level: MaybeLogLevel = None,
        discover_config_paths: Optional[bool] = None,
    ) -> None:
        """Initialize a ``doitoml`` task generator."""
        self.cwd = Path(cwd) if cwd else Path.cwd()
        try:
            self.log = self.init_log(log, log_level)
            self.entry_points = EntryPoints(self)
            self.config = self.init_config(
                config_paths or [],
                update_env=update_env,
                fail_quietly=fail_quietly,
                discover_config_paths=discover_config_paths,
            )
            # initialize late for ``entry_points`` that reference ``self.entry_points``
            self.entry_points.initialize()
            self.config.initialize()
        except DoitomlError as err:
            if fail_quietly or (
                fail_quietly is None and self.config and self.config.fail_quietly
            ):
                self.log.error("%s: %s", type(err).__name__, err)
                sys.exit(1)
            else:
                raise err

        if self.config.update_env:
            self.update_env()

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

    def init_config(
        self,
        config_paths: PathOrStrings,
        update_env: Optional[bool] = None,
        fail_quietly: Optional[bool] = None,
        discover_config_paths: Optional[bool] = None,
    ) -> Config:
        """Initialize configuration."""
        return Config(
            self,
            [(self.cwd / path).resolve() for path in config_paths],
            update_env=update_env,
            fail_quietly=fail_quietly,
            discover_config_paths=discover_config_paths,
        )

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
        value = os.environ.get(key, self.config.env.get(key, default))
        if value is None:
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
                if DOIT_TASK.ACTIONS in subtask:
                    yield self.build_subtask(subtask_name, subtask)
                else:  # pragma: no cover
                    message = "Expected a task in {subtask_name} {subtask}"
                    raise TaskError(message)

        task.__name__ = f"task_{prefix}"
        task.__doc__ = f"... {len(subtasks)} {prefix} tasks"
        return task

    def build_subtask(self, task_name: Tuple[str, ...], raw_task: Task) -> Task:
        """Build a single generated ``doit`` task."""
        name = ":".join(task_name)
        task: Task = {"name": name}
        task.update(raw_task)
        meta = cast(dict, task.get(DOIT_TASK.META, {}))
        dt_meta = meta.get(NAME, {})
        dt_cwd = dt_meta.get(DOITOML_META.CWD) or self.cwd
        dt_env = dt_meta.get(DOITOML_META.ENV, {})
        dt_log = dt_meta.get(DOITOML_META.LOG)
        cmd_env = dict(os.environ)
        cmd_env.update(dt_env)
        old_actions = task.pop(DOIT_TASK.ACTIONS)  # type: ignore
        new_actions: List[Any] = [(doit.tools.create_folder, [dt_cwd])]

        for i, action in enumerate(old_actions):
            action_actions = self.build_one_action(action, dt_cwd, cmd_env, dt_log)

            if action_actions is None:
                message = f"""{task["name"]} action {i} is not a recognized action
                {action}
                """
                raise TaskError(message)
            new_actions += action_actions

        task[DOIT_TASK.ACTIONS] = new_actions  # type: ignore
        return cast(Task, task)

    def build_one_action(
        self,
        action: Action,
        cwd: Path,
        env: Dict[str, str],
        log_paths: LogPaths,
    ) -> Optional[List[Action]]:
        """Build up a single action definition."""
        is_shell = isinstance(action, str)
        is_tokens = isinstance(action, list) and all(
            isinstance(t, (str, Path)) for t in action
        )
        if isinstance(action, dict):
            for _actor_name, actor in self.entry_points.actors.items():
                if actor.knows(cast(dict, action)):
                    return actor.perform_action(
                        action,
                        cwd,
                        env,
                        log_paths,
                    )
        if isinstance(action, (str, list)) and (is_shell or is_tokens):
            popen_kwargs = {"cwd": cwd, "env": env}
            if not any(log_paths):
                return [doit.tools.CmdAction(action, **popen_kwargs, shell=is_shell)]

            args = [action] if isinstance(action, str) else list(map(str, action))
            return [
                (
                    self.logged_action,
                    [args, log_paths, popen_kwargs],
                ),
            ]
        return None

    def logged_action(
        self,
        args: List[str],
        log_paths: LogPaths,
        popen_kwargs: Dict[str, Any],
    ) -> bool:
        """Run a process, capturing the output to files."""
        stdout, stderr = self.ensure_parents(*log_paths)

        out = stdout.open("wb") if stdout else None
        err = None
        if stderr:
            err = subprocess.STDOUT if stdout == stderr else stderr.open("wb")
        streams: Dict[str, Any] = {"stdout": out, "stderr": err}

        rc = subprocess.call(args, **streams, **popen_kwargs)  # noqa: S603

        for stream in streams.values():
            if isinstance(stream, BufferedWriter):
                stream.close()

        return rc == 0

    def ensure_parents(self, *paths: Optional[Path]) -> Tuple[Optional[Path], ...]:
        """Clean out some paths and ensure their parents."""
        for path in paths:
            if not path:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                path.unlink()
        return paths
