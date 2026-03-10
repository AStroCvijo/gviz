# Concrete graph model.

from __future__ import annotations

from datetime import date
from typing import Dict, Iterator, List, Optional, Union

from api.models import AttributeValue, Edge, Graph, Node

# ConcreteNode
class ConcreteNode(Node):
    """A concrete, mutable graph node"""

    def __init__(
        self,
        node_id: str,
        attributes: Optional[Dict[str, AttributeValue]] = None,
    ) -> None:
        if not node_id:
            raise ValueError("node_id must be a non-empty string")
        self._id = node_id
        self._attributes: Dict[str, AttributeValue] = dict(attributes or {})

    # ABC implementation
    def get_id(self) -> str:
        return self._id

    def get_attributes(self) -> Dict[str, AttributeValue]:
        return dict(self._attributes)

    # Helpers used by plugins and the CLI
    def set_attribute(self, name: str, value: AttributeValue) -> None:
        """Add or update an attribute on this node"""
        _validate_attribute_value(value)
        self._attributes[name] = value

    def remove_attribute(self, name: str) -> None:
        """Remove an attribute by name.  No-op if the attribute does not exist."""
        self._attributes.pop(name, None)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConcreteNode):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"ConcreteNode(id={self._id!r}, attrs={list(self._attributes.keys())})"


# ConcreteEdge
class ConcreteEdge(Edge):
    """A concrete, mutable graph edge"""
    def __init__(
        self,
        edge_id: str,
        source_id: str,
        target_id: str,
        directed: bool = True,
        attributes: Optional[Dict[str, AttributeValue]] = None,
    ) -> None:
        if not edge_id:
            raise ValueError("edge_id must be a non-empty string")
        if not source_id or not target_id:
            raise ValueError("source_id and target_id must be non-empty strings")
        self._id = edge_id
        self._source_id = source_id
        self._target_id = target_id
        self._directed = directed
        self._attributes: Dict[str, AttributeValue] = dict(attributes or {})

    # ABC implementation
    def get_id(self) -> str:
        return self._id

    def get_source_id(self) -> str:
        return self._source_id

    def get_target_id(self) -> str:
        return self._target_id

    def is_directed(self) -> bool:
        return self._directed

    def get_attributes(self) -> Dict[str, AttributeValue]:
        return dict(self._attributes)

    # Mutation helpers
    def set_attribute(self, name: str, value: AttributeValue) -> None:
        """Add or update an attribute on this edge."""
        _validate_attribute_value(value)
        self._attributes[name] = value

    def remove_attribute(self, name: str) -> None:
        """Remove an attribute by name.  No-op if it does not exist."""
        self._attributes.pop(name, None)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConcreteEdge):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        arrow = "→" if self._directed else "—"
        return f"ConcreteEdge(id={self._id!r}, {self._source_id!r} {arrow} {self._target_id!r})"


# ConcreteGraph
class ConcreteGraph(Graph):
    """A concrete, mutable graph that supports directed/undirected and cyclic/acyclic structures"""

    def __init__(self, directed: bool = True) -> None:
        self._directed = directed
        self._nodes: Dict[str, ConcreteNode] = {}
        self._edges: Dict[str, ConcreteEdge] = {}
        self._edge_counter: int = 0

    # ABC implementation
    def get_nodes(self) -> List[ConcreteNode]:
        return list(self._nodes.values())

    def get_edges(self) -> List[ConcreteEdge]:
        return list(self._edges.values())

    def is_directed(self) -> bool:
        return self._directed

    def get_node_by_id(self, node_id: str) -> Optional[ConcreteNode]:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> List[ConcreteNode]:
        neighbors: List[ConcreteNode] = []
        for edge in self._edges.values():
            if edge.get_source_id() == node_id:
                neighbor = self._nodes.get(edge.get_target_id())
                if neighbor is not None:
                    neighbors.append(neighbor)
            elif not self._directed and edge.get_target_id() == node_id:
                neighbor = self._nodes.get(edge.get_source_id())
                if neighbor is not None:
                    neighbors.append(neighbor)
        return neighbors

    def get_edge_by_id(self, edge_id: str) -> Optional[ConcreteEdge]:
        return self._edges.get(edge_id)

    # Mutation API
    def add_node(self, node: ConcreteNode) -> None:
        """Add a node to the graph"""
        if node.get_id() in self._nodes:
            raise ValueError(f"Node with id '{node.get_id()}' already exists")
        self._nodes[node.get_id()] = node

    def add_or_update_node(self, node: ConcreteNode) -> None:
        """Add a node, or silently replace it if the id already exists."""
        self._nodes[node.get_id()] = node

    def remove_node(self, node_id: str) -> None:
        """Remove a node by id"""
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' does not exist")
        incident = [
            e for e in self._edges.values()
            if e.get_source_id() == node_id or e.get_target_id() == node_id
        ]
        if incident:
            ids = ", ".join(e.get_id() for e in incident)
            raise ValueError(
                f"Cannot delete node '{node_id}': remove its edges first ({ids})"
            )
        del self._nodes[node_id]

    def add_edge(self, edge: ConcreteEdge) -> None:
        """Add an edge to the graph"""
        if edge.get_id() in self._edges:
            raise ValueError(f"Edge with id '{edge.get_id()}' already exists")
        if edge.get_source_id() not in self._nodes:
            raise ValueError(
                f"Source node '{edge.get_source_id()}' does not exist in the graph"
            )
        if edge.get_target_id() not in self._nodes:
            raise ValueError(
                f"Target node '{edge.get_target_id()}' does not exist in the graph"
            )
        self._edges[edge.get_id()] = edge

    def add_edge_loose(self, edge: ConcreteEdge) -> None:
        """Add an edge without checking that source/target nodes exist"""
        if edge.get_id() in self._edges:
            raise ValueError(f"Edge with id '{edge.get_id()}' already exists")
        self._edges[edge.get_id()] = edge

    def remove_edge(self, edge_id: str) -> None:
        """Remove an edge by id"""
        if edge_id not in self._edges:
            raise KeyError(f"Edge '{edge_id}' does not exist")
        del self._edges[edge_id]

    def next_edge_id(self) -> str:
        """Generate a unique edge identifier (auto-increment)."""
        self._edge_counter += 1
        return f"e{self._edge_counter}"

    # Subgraph construction
    def subgraph(self, node_ids: List[str]) -> "ConcreteGraph":
        """Return a new ConcreteGraph containing only the nodes in
        *node_ids* and the edges whose both endpoints are in *node_ids*"""
        id_set = set(node_ids)
        sub = ConcreteGraph(directed=self._directed)
        for nid in node_ids:
            node = self._nodes.get(nid)
            if node is not None:
                sub._nodes[nid] = node
        for edge in self._edges.values():
            if edge.get_source_id() in id_set and edge.get_target_id() in id_set:
                sub._edges[edge.get_id()] = edge
        return sub

    # Serialisation helpers
    def to_dict(self) -> dict:
        """Serialise the graph to a plain Python dictionary (JSON-compatible,
        except `date` values which are converted to ISO strings)"""
        def _serialize_value(v: AttributeValue):
            if isinstance(v, date):
                return v.isoformat()
            return v

        nodes_list = []
        for node in self._nodes.values():
            nodes_list.append({
                "id": node.get_id(),
                "attributes": {
                    k: _serialize_value(v)
                    for k, v in node.get_attributes().items()
                },
            })

        edges_list = []
        for edge in self._edges.values():
            edges_list.append({
                "id": edge.get_id(),
                "source": edge.get_source_id(),
                "target": edge.get_target_id(),
                "directed": edge.is_directed(),
                "attributes": {
                    k: _serialize_value(v)
                    for k, v in edge.get_attributes().items()
                },
            })

        return {
            "directed": self._directed,
            "nodes": nodes_list,
            "edges": edges_list,
        }

    # Validation
    def validate(self) -> List[str]:
        """Check graph integrity and return a list of error messages"""
        errors: List[str] = []
        for edge in self._edges.values():
            if edge.get_source_id() not in self._nodes:
                errors.append(
                    f"Edge '{edge.get_id()}' references unknown source node "
                    f"'{edge.get_source_id()}'"
                )
            if edge.get_target_id() not in self._nodes:
                errors.append(
                    f"Edge '{edge.get_id()}' references unknown target node "
                    f"'{edge.get_target_id()}'"
                )
        return errors

    def __repr__(self) -> str:
        kind = "Directed" if self._directed else "Undirected"
        return f"ConcreteGraph({kind}, nodes={len(self._nodes)}, edges={len(self._edges)})"


# Internal helper
def _validate_attribute_value(value: object) -> None:
    """Raise `TypeError` if valu* is not an allowed attribute type."""
    if not isinstance(value, (int, float, str, date)):
        raise TypeError(
            f"Attribute value must be int, float, str, or datetime.date; "
            f"got {type(value).__name__!r}"
        )
