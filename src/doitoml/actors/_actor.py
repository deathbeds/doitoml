"""Base actor for ``doitoml``."""
import abc
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from doitoml.types import ExecutionContext

if TYPE_CHECKING:
    from doitoml.doitoml import DoiTOML
    from doitoml.sources._config import ConfigSource

CallableAction = Callable[[], Optional[bool]]


class Actor:

    """A base class for a ``doitoml`` actor plugin."""

    #: a reference to the parent
    doitoml: "DoiTOML"

    #: the rank of the action
    rank = 100

    def __init__(self, doitoml: "DoiTOML") -> None:
        """Create an Actor and remember its parent."""
        self.doitoml = doitoml

    @abc.abstractmethod
    def knows(self, action: Dict[str, Any]) -> bool:
        """Whether the actor knows how to transform and perform an action."""

    @abc.abstractmethod
    def transform_action(
        self,
        source: "ConfigSource",
        action: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Expand an action dict's tokens at the end of configuration."""

    @abc.abstractmethod
    def perform_action(
        self,
        action: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> List[CallableAction]:
        """Build a function that will fully resolve the action during task building."""
