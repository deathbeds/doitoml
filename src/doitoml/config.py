"""Handles discovering, loading, and normalizing configuration."""
import os
from copy import deepcopy
from pathlib import Path
from pprint import pformat
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

if TYPE_CHECKING:
    from doitoml.doitoml import DoiTOML


from doitoml.constants import (
    DEFAULTS,
    DOIT_TASK,
    DOITOML_META,
    FALSEY,
    NAME,
)
from doitoml.errors import (
    ActionError,
    ConfigError,
    DoitomlError,
    MissingDependencyError,
    NoActorError,
    NoConfigError,
    NoTemplaterError,
    PrefixError,
    UnresolvedError,
)
from doitoml.types import (
    Action,
    LogPaths,
    PathOrString,
    PathOrStrings,
    Paths,
    PrefixedPaths,
    PrefixedStrings,
    PrefixedStringsOrPaths,
    PrefixedTaskGenerator,
    PrefixedTasks,
    Strings,
    Task,
)

from .sources._config import ConfigParser, ConfigSource
from .sources._source import Source

Parsers = Dict[str, Type[Source]]

ConfigParsers = Dict[Tuple[str], Type[ConfigSource]]

ConfigSources = Dict[str, ConfigSource]
EnvDict = Dict[str, str]


RETRIES = 11


try:
    from . import schema

    HAS_JSONSCHEMA = True
    JSONSCHEMA_ERROR = None
except MissingDependencyError as err:
    HAS_JSONSCHEMA = False
    JSONSCHEMA_ERROR = f"cannot validate: {err}"


class Config:

    """A composite configuration loaded from multiple ConfigSource."""

    doitoml: "DoiTOML"
    config_paths: Paths
    sources: ConfigSources
    tasks: PrefixedTasks
    env: EnvDict
    paths: PrefixedPaths
    cmd: PrefixedStringsOrPaths
    update_env: Optional[bool]
    fail_quietly: Optional[bool]
    discover_config_paths: Optional[bool]
    validate: bool

    def __init__(
        self,
        doitoml: "DoiTOML",
        config_paths: Paths,
        *,
        update_env: Optional[bool] = None,
        fail_quietly: Optional[bool] = None,
        discover_config_paths: Optional[bool] = None,
        validate: Optional[bool] = None,
    ) -> None:
        """Create empty configuration and discover sources."""
        self.validate = HAS_JSONSCHEMA if validate is None else validate
        self.doitoml = doitoml
        self.config_paths = config_paths
        self.sources = {}
        self.tasks = {}
        self.paths = {}
        self.env = {}
        self.cmd = {}
        self.update_env = update_env
        self.fail_quietly = fail_quietly
        self.discover_config_paths = discover_config_paths

    def to_dict(self) -> Dict[str, Any]:
        """Return a normalized subset of config data."""
        env = dict(**self.env)
        env.update(os.environ)
        return {
            "env": {k: str(v) for k, v in env.items()},
            "cmd": {":".join(k): list(map(str, v)) for k, v in self.cmd.items()},
            "paths": {":".join(k): list(map(str, v)) for k, v in self.paths.items()},
            "tasks": {":".join(k): v for k, v in self.tasks.items()},
        }

    def initialize(self) -> None:
        """Perform a few passes to configure everything."""
        # first find the env
        self.sources = self.find_config_sources()

        top_config = [*self.sources.values()][0]

        unresolved_env = self.init_env({}, RETRIES)
        if unresolved_env:
            message = (
                f"Failed to resolve environment variables: {pformat(unresolved_env)}"
            )
            raise UnresolvedError(message)

        # load other top-level config values from the first config
        for key in [DEFAULTS.UPDATE_ENV, DEFAULTS.FAIL_QUIETLY]:
            if getattr(self, key, None) is None:
                setattr(self, key, top_config.raw_config.get(key, True))

        # ...then find the paths
        unresolved_paths = self.init_paths({}, RETRIES)
        if unresolved_paths:
            message = f"Failed to resolve paths: {pformat(unresolved_paths)}"
            raise UnresolvedError(message)

        # ...then find the commands
        unresolved_commands = self.init_commands({}, RETRIES)
        if unresolved_commands:
            message = f"Failed to resolve commands: {pformat(unresolved_commands)}"
            raise UnresolvedError(message)

        # .. then find the tasks
        self.init_tasks()

        if self.validate:
            self.validate_all()

    def validate_all(self) -> None:
        """Check for validation errors."""
        schema.latest.validate(self.to_dict())

    def find_config_sources(self) -> ConfigSources:
        """Find all directly and referenced configuration sources."""
        config_sources: ConfigSources = {}
        unchecked_paths = [*self.config_paths]

        if not unchecked_paths:
            unchecked_paths += self.find_fallback_config_sources()

        if not unchecked_paths:
            path = self.doitoml.cwd / DEFAULTS.CONFIG_PATH
            if path.exists():
                unchecked_paths += [path]

        while unchecked_paths:
            config_path = unchecked_paths.pop(0)
            config_source = self.load_config_source(Path(config_path))
            self.find_one_config_source(config_source, config_sources)

        if not config_sources:
            message = "No ``doitoml`` config found"
            raise NoConfigError(message)

        return config_sources

    def find_one_config_source(
        self,
        config_source: ConfigSource,
        sources: ConfigSources,
    ) -> None:
        """Discover a config source and its potentially-nested extra sources."""
        if config_source in sources.values() or not config_source.raw_config:
            return

        self.claim_prefix(config_source, sources)

        for extra_source in config_source.extra_config_sources(self.doitoml):
            self.find_one_config_source(extra_source, sources)

    def find_fallback_config_sources(self) -> Paths:
        """Find sources."""
        unchecked = []

        if self.discover_config_paths is not False:
            for parser in self.doitoml.entry_points.config_parsers.values():
                for well_known in parser.well_known:
                    path = self.doitoml.cwd / well_known
                    if path.exists():
                        unchecked += [path]

        return unchecked

    def claim_prefix(self, source: ConfigSource, sources: ConfigSources) -> None:
        """Claim a prefix for a source."""
        prefix = source.prefix
        prefix_claimed_by = sources.get(prefix)
        if prefix_claimed_by:
            message = f"{source} cannot claim prefix '{prefix}': {prefix_claimed_by}"
            raise PrefixError(message)
        sources[prefix] = source

    def get_config_parser(self, config_path: Path) -> ConfigParser:
        """Find the config parser for a path."""
        config_parsers = self.doitoml.entry_points.config_parsers
        tried = []
        for config_parser in config_parsers.values():
            if config_parser.pattern.search(config_path.name):
                return config_parser
            tried += [config_parser.pattern.pattern]
        message = f"Cannot load {config_path}: expected one of {tried}"
        raise ConfigError(message)

    def load_config_source(self, config_path: Path) -> ConfigSource:
        """Maybe load a configuration source."""
        config_parser = self.get_config_parser(config_path)
        return config_parser(config_path)

    def init_env(self, unresolved_env: EnvDict, retries: int) -> EnvDict:
        """Initialize the global environment variable."""
        for source in self.sources.values():
            self.init_source_env(source, unresolved_env)

        while unresolved_env and retries:
            retries -= 1
            unresolved_env = self.init_env(unresolved_env, 0)

        return unresolved_env

    def init_source_env(self, source: ConfigSource, unresolved_env: EnvDict) -> None:
        """Initialize the env declared in a single source."""
        env = self.env
        raw_config = source.raw_config
        for env_key, env_value in raw_config.get("env", {}).items():
            if env_key in env:
                continue

            new_key_value = self.resolve_one_env(source, env_value)

            if new_key_value is None:
                unresolved_env[env_key] = env_value
            else:
                env[env_key] = new_key_value
                unresolved_env.pop(env_key, None)

    def resolve_one_env(self, source: ConfigSource, env_value: str) -> Optional[str]:
        """Resolve a single env member."""
        new_value = env_value
        for dsl in self.doitoml.entry_points.dsl.values():
            match = dsl.pattern.search(env_value)
            if match is not None:
                try:
                    new_value = str(dsl.transform_token(source, match, env_value)[0])
                    break
                except DoitomlError:
                    return None
        return new_value

    def init_paths(
        self,
        unresolved_paths: PrefixedStrings,
        retries: int,
    ) -> PrefixedStrings:
        """Find all paths in all sources."""
        for source in self.sources.values():
            self.init_source_paths(source, unresolved_paths)

        while unresolved_paths and retries:
            retries -= 1
            unresolved_paths = self.init_paths(
                unresolved_paths,
                0,
            )

        return unresolved_paths

    def init_commands(
        self,
        unresolved_commands: PrefixedStrings,
        retries: int,
    ) -> PrefixedStrings:
        """Find all commands in all sources."""
        for source in self.sources.values():
            self.init_source_commands(source, unresolved_commands)

        while unresolved_commands and retries:
            retries -= 1
            unresolved_commands = self.init_commands(
                unresolved_commands,
                0,
            )

        return unresolved_commands

    def init_source_paths(
        self,
        source: ConfigSource,
        unresolved_paths: PrefixedStrings,
    ) -> None:
        """Find the prefixed paths declared in a single source."""
        raw_config = source.raw_config
        path_key: str
        for path_key, path_specs in raw_config.get("paths", {}).items():
            found_paths, unresolved_specs = self.resolve_some_path_specs(
                source,
                path_specs,
                source_relative=True,
            )

            if unresolved_specs:
                unresolved_paths[source.prefix, path_key] = unresolved_specs
                continue
            self.paths[source.prefix, path_key] = sorted(
                {Path(p) for p in found_paths},
            )
            unresolved_paths.pop((source.prefix, path_key), None)

    def init_source_commands(
        self,
        source: ConfigSource,
        unresolved_commands: PrefixedStrings,
    ) -> None:
        """Find the prefixed paths declared in a single source."""
        raw_config = source.raw_config
        path_key: str
        for path_key, path_specs in raw_config.get("cmd", {}).items():
            found_cmds, unresolved_specs = self.resolve_some_path_specs(
                source,
                path_specs,
                source_relative=False,
            )

            if unresolved_specs:
                unresolved_commands[source.prefix, path_key] = unresolved_specs
                continue
            self.cmd[source.prefix, path_key] = found_cmds
            unresolved_commands.pop((source.prefix, path_key), None)

    def resolve_one_path_spec(
        self,
        source: ConfigSource,
        spec: str,
        source_relative: bool,
    ) -> Optional[PathOrStrings]:
        """Resolve a single path in a task or one of the special field tables.

        If ``source_relative``, transform unparsed strings into a path.
        """
        resolved = []
        for dsl in self.doitoml.entry_points.dsl.values():
            match = dsl.pattern.search(spec)
            if match is not None:
                resolved = dsl.transform_token(source, match, spec)
                if resolved is None:
                    return None
                break

        if resolved:
            if source_relative:
                return [(source.path.parent / r).resolve() for r in resolved]
            return resolved

        if source_relative:
            return [(source.path.parent / spec).resolve()]

        return [spec]

    def init_tasks(self) -> None:
        """Initialize all intermediate task representations."""
        for prefix, source in self.sources.items():
            raw_tasks = deepcopy(source.raw_config.get("tasks", {}))
            raw_templates = source.raw_config.get("templates", {})
            templaters = self.doitoml.entry_points.templaters
            for templater_name, templater_kinds in raw_templates.items():
                templater = templaters.get(templater_name)
                if templater is None:
                    message = (
                        f"Templater {templater_name} not one of "
                        f"""{", ".join(templaters.keys())}"""
                    )
                    raise NoTemplaterError(message)
                templater_tasks = deepcopy(templater_kinds.get("tasks", {}))
                for task_name, task in templater_tasks.items():
                    templated = templater.transform_task(source, task)
                    if isinstance(templated, dict):
                        raw_tasks[task_name] = templated
                    else:
                        raw_tasks[task_name] = {t["name"]: t for t in templated}

            for task_prefix, task in self.resolve_one_task_or_group(
                source,
                (prefix,),
                raw_tasks,
            ):
                claimed_prefix = self.tasks.get(task_prefix)
                if claimed_prefix:  # pragma: no cover
                    # not sure how we'd get here
                    pfx = ":".join(task_prefix)
                    message = f"""{source} cannot claim {pfx}: {claimed_prefix}"""
                    raise ConfigError(message)
                self.tasks[task_prefix] = task

    def resolve_one_task_or_group(
        self,
        source: ConfigSource,
        prefixes: Tuple[str, ...],
        task_or_group: Union[Task, Dict[str, Task]],
    ) -> PrefixedTaskGenerator:
        """Resolve a task or task group in a prefix."""
        if not isinstance(task_or_group, dict):
            message = f"{source} task {prefixes} is not a dict: {task_or_group}"
            raise ConfigError(message)

        maybe_old_actions = task_or_group.get(DOIT_TASK.ACTIONS, [])

        meta = cast(dict, task_or_group.get(DOIT_TASK.META))

        if isinstance(meta, dict) and NAME in meta:
            dt_meta = meta[NAME]
            if isinstance(dt_meta, dict) and DOITOML_META.SKIP in dt_meta:
                skip = dt_meta.get(DOITOML_META.SKIP)
                if str(skip).strip().lower() not in FALSEY:
                    return

        if maybe_old_actions:
            task = cast(Task, task_or_group)
            yield from self.resolve_one_task(source, prefixes, task)
            return

        group = cast(Dict[str, Task], task_or_group)
        for subtask_prefix, subtask_or_group in group.items():
            for subtask_prefixes, subtask in self.resolve_one_task_or_group(
                source,
                (*prefixes, subtask_prefix),
                subtask_or_group,
            ):
                yield subtask_prefixes, subtask

    def resolve_one_task(
        self,
        source: ConfigSource,
        prefixes: Tuple[str, ...],
        task: Task,
    ) -> PrefixedTaskGenerator:
        """Resolve a single simple task."""
        old_actions = cast(List[Action], task[DOIT_TASK.ACTIONS])  # type: ignore
        new_task = self.normalize_task_meta(source, task)
        all_unresolved_specs: List[str] = []
        new_actions: List[Action] = []

        for action in old_actions:
            action_actions, unresolved_specs = self.resolve_one_action(source, action)
            if unresolved_specs:
                all_unresolved_specs += unresolved_specs
                continue
            new_actions += action_actions

        new_task["actions"] = new_actions

        for field in DOIT_TASK.RELATIVE_LISTS:
            specs: Strings = task.get(field, [])  # type: ignore
            new_paths, unresolved_specs = self.resolve_one_task_field(source, specs)
            if unresolved_specs:
                all_unresolved_specs += unresolved_specs
                continue
            new_task[field] = new_paths  # type: ignore

        if all_unresolved_specs:
            message = (
                f"{source} task {prefixes} had unresolved paths:"
                f" {all_unresolved_specs}"
            )
            raise UnresolvedError(message)

        yield prefixes, new_task

    def normalize_task_meta(
        self,
        source: ConfigSource,
        task: Task,
    ) -> Task:
        """Normalize task metadata."""
        new_task = deepcopy(task)
        meta = cast(dict, cast(dict, new_task).setdefault(DOIT_TASK.META, {}))
        dt_meta = cast(dict, meta.setdefault(NAME, {}))
        dt_cwd = Path(dt_meta.get(DOITOML_META.CWD, source.path.parent))
        dt_log_paths = self.build_log_paths(dt_meta.get(DOITOML_META.LOG), dt_cwd)
        dt_meta[DOITOML_META.LOG] = dt_log_paths
        dt_meta[DOITOML_META.CWD] = dt_cwd
        env = dt_meta.setdefault(DOITOML_META.ENV, {})
        for env_key, env_value in env.items():
            new_key_value = self.resolve_one_env(source, env_value)
            env[env_key] = env_value if new_key_value is None else new_key_value
        return new_task

    def build_log_paths(
        self,
        log: Optional[Union[PathOrString, List[PathOrString]]],
        cwd: Path,
    ) -> LogPaths:
        """Set up proper path behavior from log metadata."""
        if not log:
            return (None, None)
        stdout_path = None
        stderr_path = None
        if isinstance(log, (str, Path)) and log:
            stderr_path = stdout_path = cwd / log
        else:
            stdout_path, stderr_path = (
                cwd / stream if stream else None for stream in log  # type: ignore
            )

        for path in [stderr_path, stdout_path]:
            if path and path.is_dir():
                message = f"A log path was a directory: {path}"
                raise ConfigError(message)

        if stderr_path is None and stdout_path is None:
            message = f"Expected log to be a string, or {log}"
            raise ConfigError(message)
        return stdout_path, stderr_path

    def resolve_one_action(
        self,
        source: ConfigSource,
        action: Any,
    ) -> Tuple[List[Any], Strings]:
        """Expand the members of a single action."""
        if isinstance(action, str):
            # leave raw strings to doit
            return [action], []

        if isinstance(action, list):
            return self.resolve_one_token_action(source, action)

        if isinstance(action, dict):
            return self.resolve_one_dict_action(source, action)

        message = f"Unexpected {action} in {source}"
        raise ActionError(message)

    def resolve_one_token_action(
        self,
        source: ConfigSource,
        action: Any,
    ) -> Tuple[List[Any], Strings]:
        """Resolve an action made of shell tokens."""
        unresolved_specs: Strings = []
        new_tokens: PathOrStrings = []
        for token in action:
            token_tokens = self.resolve_one_path_spec(
                source,
                str(token),
                source_relative=False,
            )
            if token_tokens:
                new_tokens += token_tokens
            else:
                unresolved_specs += [token]

        return [new_tokens], unresolved_specs

    def resolve_one_dict_action(
        self,
        source: ConfigSource,
        action: Any,
    ) -> Tuple[List[Any], Strings]:
        """Resolve an action by an actor."""
        tried = []
        for actor_name, actor in self.doitoml.entry_points.actors.items():
            if actor.knows(action):
                actor_action = actor.transform_action(source, action)
                return actor_action, []
            tried += [actor_name]

        message = f"No actor knew how to perform {action}, tried: {tried}"
        raise NoActorError(message)

    def resolve_one_task_field(
        self,
        source: ConfigSource,
        specs: List[str],
    ) -> Tuple[PathOrStrings, Strings]:
        """Expand the members of a single field."""
        return self.resolve_some_path_specs(source, specs, source_relative=True)

    def resolve_some_path_specs(
        self,
        source: ConfigSource,
        specs: List[str],
        source_relative: bool,
    ) -> Tuple[List[Any], Strings]:
        """Resolve a list of path specs."""
        new_paths: PathOrStrings = []
        unresolved_specs = []
        for spec in specs:
            spec_paths = self.resolve_one_path_spec(
                source,
                spec,
                source_relative=source_relative,
            )
            if not spec_paths:
                unresolved_specs += [spec]
                continue
            new_paths += spec_paths
        return new_paths, unresolved_specs
