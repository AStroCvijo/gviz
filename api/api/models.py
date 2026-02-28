# Graph data model abstractions.

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, Iterator, List, Optional, Union

# Supported values
AttributeValue = Union[int, float, str, date]


# Abstract Node
class Node(ABC):

    @abstractmethod
    def get_id(self) -> str:
        """Return the unique identifier of this node. """

    @abstractmethod
    def get_attributes(self) -> Dict[str, AttributeValue]:
        """Return all attributes of this node as a dictionary"""

    def get_attribute(self, name: str) -> Optional[AttributeValue]:
        """Return a single attribute value by name, or ``None`` if missing."""
        return self.get_attributes().get(name)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.get_id()!r})"


# Abstract Edge
class Edge(ABC):
    """Abstract base class for a graph edge (arc / link)."""

    @abstractmethod
    def get_id(self) -> str:
        """Return the unique identifier of this edge"""

    @abstractmethod
    def get_source_id(self) -> str:
        """Return the identifier of the source (tail) node"""

    @abstractmethod
    def get_target_id(self) -> str:
        """Return the identifier of the target (head) node"""

    @abstractmethod
    def is_directed(self) -> bool:
        """Return ``True`` if this edge is directed (source → target)"""

    @abstractmethod
    def get_attributes(self) -> Dict[str, AttributeValue]:
        """Return all attributes of this edge as a dictionary"""

    def get_attribute(self, name: str) -> Optional[AttributeValue]:
        """Return a single attribute value by name, or ``None`` if missing."""
        return self.get_attributes().get(name)

    def __repr__(self) -> str:
        arrow = "→" if self.is_directed() else "—"
        return (
            f"{self.__class__.__name__}"
            f"({self.get_source_id()!r} {arrow} {self.get_target_id()!r})"
        )

# Abstract Graph
class Graph(ABC):
    """Abstract base class for a graph"""

    @abstractmethod
    def get_nodes(self) -> List[Node]:
        """Return all nodes in the graph"""

    @abstractmethod
    def get_edges(self) -> List[Edge]:
        """Return all edges in the graph"""

    @abstractmethod
    def is_directed(self) -> bool:
        """Return `True` if the graph is a directed graph (digraph)"""

    @abstractmethod
    def get_node_by_id(self, node_id: str) -> Optional[Node]:
        """Return the node with the given identifier, or `None`"""

    @abstractmethod
    def get_neighbors(self, node_id: str) -> List[Node]:
        """Return all nodes directly reachable from *node_id*"""

    # Convenience helpers (non-abstract, built on top of the abstract API)
    def get_edges_from(self, node_id: str) -> List[Edge]:
        """Return edges whose source is *node_id* (directed)"""
        result: List[Edge] = []
        for edge in self.get_edges():
            if edge.get_source_id() == node_id:
                result.append(edge)
            elif not self.is_directed() and edge.get_target_id() == node_id:
                result.append(edge)
        return result

    def node_count(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self.get_nodes())

    def edge_count(self) -> int:
        """Return the number of edges in the graph."""
        return len(self.get_edges())

    def iter_nodes(self) -> Iterator[Node]:
        """Iterate over all nodes."""
        return iter(self.get_nodes())

    def iter_edges(self) -> Iterator[Edge]:
        """Iterate over all edges."""
        return iter(self.get_edges())

    def __repr__(self) -> str:
        kind = "Directed" if self.is_directed() else "Undirected"
        return (
            f"{self.__class__.__name__}"
            f"({kind}, nodes={self.node_count()}, edges={self.edge_count()})"
        )
