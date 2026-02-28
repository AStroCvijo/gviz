#Plugin interface abstractions.

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from api.models import Graph

# Entry-point group constants
DATA_SOURCE_ENTRY_POINT_GROUP = "gviz.data_source"

VISUALIZER_ENTRY_POINT_GROUP = "gviz.visualizer"

# Parameter descriptor
class PluginParameter:
    """Descriptor for a single plugin input parameter"""

    def __init__(
        self,
        name: str,
        label: str,
        description: str = "",
        required: bool = True,
        default: Any = None,
        param_type: type = str,
    ) -> None:
        self.name = name
        self.label = label
        self.description = description
        self.required = required
        self.default = default
        self.param_type = param_type

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the descriptor to a plain dictionary for JSON/template rendering."""
        return {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "required": self.required,
            "default": self.default,
            "param_type": self.param_type.__name__,
        }

    def __repr__(self) -> str:
        return f"PluginParameter(name={self.name!r}, required={self.required})"


# DataSourcePlugin
class DataSourcePlugin(ABC):
    """Abstract base class for data-source plugins"""

    @abstractmethod
    def get_name(self) -> str:
        """Return the unique  name of this plugin"""

    @abstractmethod
    def get_description(self) -> str:
        """Return a human-readable description of this data source"""

    @abstractmethod
    def get_parameters(self) -> List[PluginParameter]:
        """Return the list of parameters that the plugin requires from the user"""

    @abstractmethod
    def load(self, **kwargs: Any) -> Graph:
        """Parse the data source and return a :class:`~api.models.Graph`"""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.get_name()!r})"

# VisualizerPlugin
class VisualizerPlugin(ABC):
    """Abstract base class for visualiser plugins"""

    @abstractmethod
    def get_name(self) -> str:
        """Return the unique name of this plugin"""

    @abstractmethod
    def get_description(self) -> str:
        """Return a human-readable description of the visualisation style"""

    @abstractmethod
    def render(self, graph: Graph) -> str:
        """Render *graph* as an HTML string"""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.get_name()!r})"
