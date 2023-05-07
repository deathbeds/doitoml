"""Handles discovering, loading, and normalizing configuration."""
import json
import os
import warnings
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

from .constants import (
    DEFAULTS,
    DOIT_TASK,
    DOITOML_META,
    NAME,
)
from .errors import (
    ActionError,
    ConfigError,
    DoitomlError,
    MissingDependencyError,
    NoActorError,
    NoConfigError,
    NoTemplaterError,
    PrefixError,
    SkipError,
    TemplaterError,
    UnresolvedError,
    UnsafePathError,
)
from .schema._v0_schema import DoitomlSchema
from .sources._config import ConfigParser, ConfigSource
from .sources._source import Source
from .types import (
    Action,
    LogPaths,
    PathOrStrings,
    Paths,
    PrefixedStrings,
    PrefixedTaskGenerator,
    PrefixedTasks,
    PrefixedTemplates,
    Strings,
    Task,
)
from .utils.json import to_json

if TYPE_CHECKING:
    from .doitoml import DoiTOML


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
    paths: PrefixedStrings
    templates: PrefixedTemplates
    tokens: PrefixedStrings
    update_env: Optional[bool]
    fail_quietly: Optional[bool]
    discover_config_paths: Optional[bool]
    validate: Optional[bool]
    safe_paths: List[str]

    def __init__(
        self,
        doitoml: "DoiTOML",
        config_paths: Paths,
        *,
        update_env: Optional[bool] = None,
        fail_quietly: Optional[bool] = None,
        discover_config_paths: Optional[bool] = None,
        validate: Optional[bool] = None,
        safe_paths: Optional[List[str]] = None,
    ) -> None:
        """Create empty configuration and discover sources."""
        self.validate = validate
        self.doitoml = doitoml
        self.config_paths = config_paths
        self.sources = {}
        self.tasks = {}
        self.paths = {}
        self.env = {}
        self.tokens = {}
        self.templates = {}
        self.update_env = update_env
        self.fail_quietly = fail_quietly
        self.discover_config_paths = discover_config_paths
        self.safe_paths = safe_paths or []

    def to_dict(self) -> DoitomlSchema:
        """Return a normalized subset of config data."""
        env = dict(**self.env)
        env.update(os.environ)

        as_dict: DoitomlSchema = to_json(
            {
                "env": env,
                "tokens": {":".join(k): v for k, v in self.tokens.items()},
                "paths": {":".join(k): v for k, v in self.paths.items()},
                "templates": self.templates,
                "tasks": {":".join(k): v for k, v in self.tasks.items()},
            },
        )

        return as_dict

    def initialize(self) -> None:
        """Perform a few passes to configure everything."""
        self.sources = self.find_config_sources()
        # load top-level config values from the first config
        top_config = [*self.sources.values()][0]
        for key in DEFAULTS.ALL_FROM_FIRST_CONFIG:
            if getattr(self, key, None) is None:
                setattr(self, key, top_config.raw_config.get(key, True))

        unresolved_env: EnvDict = {}
        unresolved_paths: PrefixedStrings = {}
        unresolved_tokens: PrefixedStrings = {}
        retry = RETRIES

        # .. allow some retries for cross (but not circular) references
        while retry:
            retry -= 1
            try:
                unresolved_env = self.init_env(unresolved_env, RETRIES)
                unresolved_paths = self.init_paths(unresolved_paths, RETRIES)
                unresolved_tokens = self.init_tokens(unresolved_tokens, RETRIES)
            except UnresolvedError:  # pragma: no cover
                pass
            if not any([unresolved_env, unresolved_paths, unresolved_tokens]):
                break

        if not retry:
            message = [f"Gave up after {RETRIES} retries!"]
            if unresolved_env:
                message += [
                    f"Failed to resolve environment variables: "
                    f"{pformat(unresolved_env)}",
                ]

            if unresolved_paths:
                message += [f"Failed to resolve paths: {pformat(unresolved_paths)}"]

            if unresolved_tokens:
                message += [
                    f"Failed to resolve tokens: {pformat(unresolved_tokens)}",
                ]

            raise UnresolvedError("\n".join(message))

        # ... then templates
        self.init_templates()

        # ... then find the tasks
        self.init_tasks()

        self.maybe_validate()

    def maybe_validate(self) -> None:
        """Validate if requested, or."""
        if self.validate is False:
            return

        try:
            from .schema.validator import latest

            has_jsonschema = True
            jsonschema_error = None
        except MissingDependencyError as err:
            has_jsonschema = False
            jsonschema_error = str(err)

        if not has_jsonschema:  # pragma: no cover
            message = (
                f"Validation was requested, but cannot validate: {jsonschema_error}"
            )
            warnings.warn(message, stacklevel=1)
            return

        latest.validate(self.to_dict())

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

        if unchecked_paths and not self.safe_paths:
            self.safe_paths = [str(unchecked_paths[0].parent.as_posix())]

        while unchecked_paths:
            config_path = unchecked_paths.pop(0)
            config_source = self.load_config_source(
                Path(self.check_safe_path(str(config_path.as_posix()))),
            )
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
                self.doitoml.log.info(
                    "$%s already set to `%s`: not setting with `%s` from %s",
                    env_key,
                    env[env_key],
                    env_value,
                    source,
                )
                continue

            new_key_value = self.resolve_one_env(source, env_value)

            if new_key_value is None:
                unresolved_env[env_key] = env_value
            else:
                env[env_key] = new_key_value
                unresolved_env.pop(env_key, None)

    def resolve_one_env(self, source: ConfigSource, env_value: Any) -> Optional[str]:
        """Resolve a single env member."""
        new_value = str(env_value)
        for dsl in self.doitoml.entry_points.dsl.values():
            match = dsl.pattern.search(new_value)
            if match is not None:
                try:
                    resolved = dsl.transform_token(
                        source,
                        match,
                        new_value or env_value,
                    )
                    if resolved is None:  # pragma: no cover
                        return None
                    return str(resolved[0])
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

    def check_safe_path(self, path: str) -> str:
        """Check if some paths are safe."""
        if any(path.startswith(safe) for safe in self.safe_paths):
            return path

        nl = "\n  -"
        message = (
            f"The path is outside the known `safe_paths`: {path}"
            "\n"
            f"""{nl}{nl.join(self.safe_paths)}"""
        )
        raise UnsafePathError(message)

    def init_tokens(
        self,
        unresolved_tokens: PrefixedStrings,
        retries: int,
    ) -> PrefixedStrings:
        """Find all commands in all sources."""
        for source in self.sources.values():
            self.init_source_tokens(source, unresolved_tokens)

        while unresolved_tokens and retries:
            retries -= 1
            unresolved_tokens = self.init_tokens(
                unresolved_tokens,
                0,
            )

        return unresolved_tokens

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
                {Path(p).as_posix() for p in found_paths},
            )
            unresolved_paths.pop((source.prefix, path_key), None)

    def init_source_tokens(
        self,
        source: ConfigSource,
        unresolved_tokens: PrefixedStrings,
    ) -> None:
        """Find the prefixed paths declared in a single source."""
        raw_config = source.raw_config
        path_key: str
        for path_key, path_specs in raw_config.get(DEFAULTS.TOKENS, {}).items():
            found_tokens, unresolved_specs = self.resolve_some_path_specs(
                source,
                path_specs,
                source_relative=False,
            )

            if unresolved_specs:
                unresolved_tokens[source.prefix, path_key] = unresolved_specs
                continue
            self.tokens[source.prefix, path_key] = found_tokens
            unresolved_tokens.pop((source.prefix, path_key), None)

    def resolve_one_path_spec(
        self,
        source: ConfigSource,
        spec: str,
        source_relative: bool,
        cwd: Optional[Path] = None,
    ) -> Optional[Strings]:
        """Resolve a single path in a task or one of the special field tables.

        If ``source_relative``, transform unparsed strings into a path.
        """
        cwd = cwd or source.path.parent

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
                return [
                    self.check_safe_path((cwd / r).resolve().as_posix())
                    for r in resolved
                ]
            return resolved

        if source_relative:
            return [self.check_safe_path((cwd / spec).resolve().as_posix())]

        return [spec]

    def init_templates(self) -> None:
        """Copy templates (for now)."""
        for prefix, source in self.sources.items():
            raw_templates = source.raw_config.get("templates", {})
            if raw_templates:
                self.templates[prefix] = raw_templates

    def init_tasks(self) -> None:
        """Initialize all intermediate task representations."""
        for prefix, source in self.sources.items():
            raw_tasks = deepcopy(source.raw_config.get("tasks", {}))

            if prefix in self.templates:
                raw_templates = self.templates[prefix]
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

                    if not isinstance(templater_tasks, dict):
                        message = (
                            f"Expected dictionary of tasks in {source}, found: "
                            f"{templater_tasks}"
                        )
                        raise TemplaterError(message)
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

        maybe_old_actions: Optional[List[Action]] = task_or_group.get(
            DOIT_TASK.ACTIONS,
        )  # type: ignore

        meta = cast(dict, task_or_group.get(DOIT_TASK.META))

        if isinstance(meta, dict) and NAME in meta:
            dt_meta = meta[NAME]
            if isinstance(dt_meta, dict) and DOITOML_META.SKIP in dt_meta:
                skip = dt_meta.get(DOITOML_META.SKIP, "0")
                if self.resolve_one_skip(source, skip):
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

    def resolve_one_skip(self, source: ConfigSource, skip: Any) -> bool:
        """Maybe skip discovery of task (and all its children)."""
        if skip is None:
            return False
        if isinstance(skip, (int, bool, float)):
            return bool(skip)
        if isinstance(skip, str):
            found = self.resolve_one_path_spec(source, skip, source_relative=False)
            if not found:  # pragma: no cover
                return False
            json_val = json.loads(str(found[0]).lower().strip())
            return bool(json_val)
        if isinstance(skip, dict):
            for key, skipper in self.doitoml.entry_points.skippers.items():
                if key in skip:
                    return skipper.should_skip(source, skip[key])

        message = f"Skip in {source} is ambiguous: {skip}"
        raise SkipError(message)

    def resolve_one_task(
        self,
        source: ConfigSource,
        prefixes: Tuple[str, ...],
        task: Task,
    ) -> PrefixedTaskGenerator:
        """Resolve a single simple task."""
        new_task = self.normalize_task_meta(source, task)
        unresolved: List[Any] = []
        unresolved += self.resolve_task_actions(source, new_task)
        unresolved += self.resolve_task_uptodate(source, new_task)

        for field in DOIT_TASK.RELATIVE_LISTS:
            unresolved += self.resolve_one_task_list_field(
                source,
                new_task,
                field,
            )

        if unresolved:
            message = f"{source} task {prefixes} had unresolved paths: {unresolved}"
            raise UnresolvedError(message)

        yield prefixes, new_task

    def resolve_task_actions(self, source: ConfigSource, task: Task) -> List[str]:
        """Get the new actions (and unresolved paths) for a task."""
        new_actions: List[Action] = []

        for action in task[DOIT_TASK.ACTIONS]:
            action_actions, unresolved_specs = self.resolve_one_action(source, action)
            if unresolved_specs:
                return unresolved_specs
            new_actions += action_actions

        task[DOIT_TASK.ACTIONS] = new_actions

        return []

    def resolve_task_uptodate(self, source: ConfigSource, task: Task) -> List[str]:
        """Transform some uptodate values."""
        new_uptodate: List[Any] = []
        for old_uptodate in task.get(DOIT_TASK.UPTODATE, []):
            if isinstance(old_uptodate, dict):
                uptodate, unresolved = self.resolve_one_uptodate(source, old_uptodate)
                if unresolved:
                    return unresolved
                new_uptodate += [uptodate]
            else:
                new_uptodate += [old_uptodate]

        if new_uptodate:
            task[DOIT_TASK.UPTODATE] = new_uptodate

        return []

    def resolve_one_uptodate(
        self,
        source: ConfigSource,
        uptodate: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Strings]:
        """Transform a single uptodate."""
        for key, updater in self.doitoml.entry_points.updaters.items():
            args = uptodate.get(key)
            if args:
                return {key: updater.transform_uptodate(source, args)}, []

        return {}, [*uptodate.keys()]

    def normalize_task_meta(self, source: ConfigSource, task: Task) -> Task:
        """Normalize task metadata."""
        new_task = deepcopy(task)
        meta = cast(dict, cast(dict, new_task).setdefault(DOIT_TASK.META, {}))
        dt_meta = cast(dict, meta.setdefault(NAME, {}))
        raw_cwd = self.resolve_one_path_spec(
            source,
            dt_meta.get(DOITOML_META.CWD, str(source.path.parent)),
            source_relative=True,
        )
        dt_cwd = Path(
            self.check_safe_path(raw_cwd[0] if raw_cwd else str(source.path.parent)),
        )
        dt_log_paths = self.build_log_paths(
            source,
            dt_meta.get(DOITOML_META.LOG),
            dt_cwd,
        )
        dt_meta[DOITOML_META.LOG] = dt_log_paths
        dt_meta[DOITOML_META.CWD] = dt_cwd
        dt_meta[DOITOML_META.SOURCE] = source
        env = dt_meta.setdefault(DOITOML_META.ENV, {})
        for env_key, env_value in env.items():
            new_key_value = self.resolve_one_env(source, env_value)
            env[env_key] = env_value if new_key_value is None else new_key_value
        return new_task

    def build_log_paths(
        self,
        source: ConfigSource,
        log: Optional[Union[str, List[str]]],
        cwd: Path,
    ) -> LogPaths:
        """Set up proper path behavior from log metadata."""
        if not log:
            return (None, None)

        if isinstance(log, str) and log:
            log = [log, log]

        maybe_paths: List[Optional[Path]] = [None, None]

        for i, stream in enumerate(log):
            if not stream:
                continue
            maybe_stream_path = self.resolve_one_path_spec(
                source,
                str(stream),
                source_relative=True,
                cwd=cwd,
            )

            if not maybe_stream_path:  # pragma: no cover
                message = f"Unresolved log path {stream}"
                raise ConfigError(message)

            maybe_paths[i] = Path(self.check_safe_path(maybe_stream_path[0]))

        return self.check_log_paths(*maybe_paths)

    def check_log_paths(self, stderr_path: Any, stdout_path: Any) -> LogPaths:
        """Verify log paths."""
        for path in [stderr_path, stdout_path]:
            if path and path.is_dir():
                message = f"A log path was a directory: {path}"
                raise ConfigError(message)

        if stderr_path is None and stdout_path is None:
            message = "Expected log to be a string, or list of strings"
            raise ConfigError(message)
        return cast(LogPaths, (stderr_path, stdout_path))

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

    def resolve_one_task_list_field(
        self,
        source: ConfigSource,
        task: Task,
        field: str,
    ) -> Strings:
        """Expand the members of a single field."""
        specs: Strings = task.get(field, [])  # type: ignore
        new_paths, unresolved_specs = self.resolve_some_path_specs(
            source,
            specs,
            source_relative=True,
        )
        if unresolved_specs:
            return unresolved_specs
        task[field] = new_paths  # type: ignore
        return []

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
