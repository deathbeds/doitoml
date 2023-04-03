"""Handles discovering, loading, and normalizing configuration."""
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

if TYPE_CHECKING:  # pragma: no cover
    from doitoml.doitoml import DoiTOML


from doitoml.constants import (
    DEFAULT_CONFIG_PATH,
    DOIT_ACTIONS,
    DOIT_PATH_RELATIVE_LISTS,
    DOITOML_FAIL_QUIETLY,
    DOITOML_UPDATE_ENV,
)
from doitoml.errors import (
    ConfigError,
    DoitomlError,
    NoConfigError,
    PrefixError,
    UnresolvedError,
)
from doitoml.types import (
    Action,
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

from .sources._config import ConfigSource
from .sources._source import Source

Parsers = Dict[str, Type[Source]]

ConfigParsers = Dict[Tuple[str], Type[ConfigSource]]

ConfigSources = Dict[str, ConfigSource]
EnvDict = Dict[str, str]


RETRIES = 11


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

    def __init__(
        self,
        doitoml: "DoiTOML",
        config_paths: Paths,
        *,
        update_env: Optional[bool] = None,
        fail_quietly: Optional[bool] = None,
        discover_config_paths: Optional[bool] = None,
    ) -> None:
        """Create empty configuration and discover sources."""
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
        for key in [DOITOML_UPDATE_ENV, DOITOML_FAIL_QUIETLY]:
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

    def find_config_sources(self) -> ConfigSources:
        """Find all directly and referenced configuration sources."""
        sources: ConfigSources = {}
        unchecked = [*self.config_paths]

        if not unchecked:
            unchecked += self.find_fallback_config_sources()

        if not unchecked:
            path = self.doitoml.cwd / DEFAULT_CONFIG_PATH
            if path.exists():
                unchecked += [path]

        checked = []

        while unchecked:
            config_path = unchecked.pop(0)
            checked += [config_path]
            source = self.load_config_source(Path(config_path))
            if source in sources.values() or not source.raw_config:
                continue

            self.claim_prefix(source, sources)

            for extra_path in source.extra_config_paths:
                if extra_path not in checked and extra_path not in unchecked:
                    unchecked.append(extra_path)

        if not sources:
            message = "No config found in any of: " + (
                "\n".join(
                    [""] + [f"- {p}" for p in checked],
                )
            )
            raise NoConfigError(message)

        return sources

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

    def load_config_source(self, config_path: Path) -> ConfigSource:
        """Maybe load a configuration source."""
        config_parsers = self.doitoml.entry_points.config_parsers
        tried = []
        for config_parser in config_parsers.values():
            if config_parser.pattern.search(config_path.name):
                source = config_parser(config_path)
                return source
            tried += [config_parser.pattern.pattern]
        message = f"Cannot load {config_path}: expected one of {tried}"
        raise ConfigError(message)

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
        for dsl in self.doitoml.entry_points.dsl.values():
            match = dsl.pattern.search(env_value)
            if match is not None:
                try:
                    return str(dsl.transform_token(source, match, env_value)[0])
                except DoitomlError:
                    return None
        return env_value

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
            found_paths: PathOrStrings = []
            unresolved_specs: List[str] = []
            for spec in path_specs:
                spec_paths = self.resolve_one_path_spec(
                    source,
                    spec,
                    source_relative=True,
                )
                if spec_paths:
                    found_paths += spec_paths
                else:
                    unresolved_specs += [spec]

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
            found_cmds: PathOrStrings = []
            unresolved_specs: List[str] = []
            for spec in path_specs:
                spec_paths = self.resolve_one_path_spec(
                    source,
                    spec,
                    source_relative=False,
                )
                if spec_paths:
                    found_cmds += spec_paths
                else:
                    unresolved_specs += [spec]

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
            raw_tasks = source.raw_config.get("tasks", {})
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
        maybe_old_actions = task_or_group.get(DOIT_ACTIONS, [])
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
        old_actions = cast(List[Action], task[DOIT_ACTIONS])  # type: ignore
        new_task = deepcopy(task)
        all_unresolved_specs: List[str] = []
        new_actions: List[Action] = []

        for action in old_actions:
            action_actions, unresolved_specs = self.resolve_one_action(source, action)
            if unresolved_specs:
                all_unresolved_specs += unresolved_specs
                continue
            new_actions += action_actions

        new_task["actions"] = new_actions

        for field in DOIT_PATH_RELATIVE_LISTS:
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

    def resolve_one_action(
        self,
        source: ConfigSource,
        action: Any,
    ) -> Tuple[List[Any], Strings]:
        """Expand the members of a single action."""
        if isinstance(action, str):
            # leave raw strings to doit
            return [action], []

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

    def resolve_one_task_field(
        self,
        source: ConfigSource,
        specs: List[str],
    ) -> Tuple[PathOrStrings, Strings]:
        """Expand the members of a single field."""
        new_paths: PathOrStrings = []
        unresolved_specs = []

        for spec in specs:
            spec_paths = self.resolve_one_path_spec(
                source,
                spec,
                source_relative=True,
            )
            if not spec_paths:
                unresolved_specs += [spec]
                continue
            new_paths += spec_paths
        return new_paths, unresolved_specs
