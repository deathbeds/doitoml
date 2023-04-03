"""Custom exceptions for ``doitoml``."""


class DoitomlError(ValueError):

    """Some kind of error in ``doitoml``."""


class ConfigError(DoitomlError):

    """An error related to configuration."""


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
