"""Custom exceptions for ``doitoml``."""


class DoitomlError(ValueError):

    """Some kind of error in ``doitoml``."""


class PyError(DoitomlError):

    """An error related to discovering and calling user-defined Python functions."""


class SchemaError(DoitomlError):

    """An error related to a non-conforming ``doitoml`` configuration."""


class MissingDependencyError(ValueError):

    """An error related to a missing (optional) dependency."""


class ConfigError(DoitomlError):

    """An error related to configuration."""


class UnsafePathError(ConfigError):

    """An error related to unsafe paths."""


class SkipError(ConfigError):

    """An error related to an ambiguous skip."""


class NoConfigError(ConfigError):

    """An error when no configuration at all is found."""


class UnresolvedError(ConfigError):

    """A config error related to unresolved values."""


class PrefixError(ConfigError):

    """A config error related to prefixes of configuration files."""


class DslError(ConfigError):

    """An error related to a domain-specific language plugin during configuration."""


class EnvVarError(ConfigError):

    """An error related to an environment variable during configuration."""


class EntryPointError(DoitomlError):

    """An error related to initializing entry points."""


class ParseError(DoitomlError):

    """An error related to source parsing."""


class TaskError(DoitomlError):

    """An error related to generating valid tasks."""


class UpdaterError(TaskError):

    """An error related to an up-to-date checker."""


class MetaError(TaskError):

    """An error related to ``doitoml`` task metadata."""


class TemplaterError(ConfigError):

    """An error related to templates."""


class JsonEError(ConfigError):

    """An error related to JSON-e."""


class NoTemplaterError(TemplaterError):

    """An error related to missing templaters."""


class ActionError(TaskError):

    """An error related to task actions."""


class ActorError(ActionError):

    """An error related to custom actor actions."""


class NoActorError(ActorError):

    """An error related to a missing actor."""


class Jinja2Error(ActorError):

    """An error related to Jinja2 templates."""
