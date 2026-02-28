# Graph search and attribute filtering.

from __future__ import annotations

import re
from datetime import date
from typing import Callable, List, Optional

from api.exceptions import FilterError
from api.models import AttributeValue, Graph
from gviz_platform.graph import ConcreteGraph

# Supported comparators
_COMPARATORS = [">=", "<=", "!=", "==", ">", "<"]

# Regex that matches the filter expression (longest operators first)
_FILTER_RE = re.compile(
    r"^\s*(\w+)\s*(>=|<=|!=|==|>|<)\s*(.+?)\s*$"
)

# FilterEngine
class FilterEngine:
    """Stateless engine for graph search and filter operations"""

    # Search
    def search(self, graph: Graph, query: str) -> ConcreteGraph:
        """Return a subgraph containing nodes whose attributes match query"""
        if not query or not query.strip():
            return _to_concrete_subgraph(graph, [n.get_id() for n in graph.get_nodes()])

        q = query.strip().lower()
        matching_ids: List[str] = []

        for node in graph.get_nodes():
            for attr_name, attr_value in node.get_attributes().items():
                if q in attr_name.lower() or q in str(attr_value).lower():
                    matching_ids.append(node.get_id())
                    break

        return _to_concrete_subgraph(graph, matching_ids)

    # Filter
    def filter(self, graph: Graph, expression: str) -> ConcreteGraph:
        """Return a subgraph containing nodes that satisfy expression"""
        attr_name, comparator, raw_value = _parse_expression(expression)
        compare_fn = _COMPARE_FUNCTIONS[comparator]

        matching_ids: List[str] = []

        for node in graph.get_nodes():
            attrs = node.get_attributes()
            if attr_name not in attrs:
                continue
            attr_value = attrs[attr_name]
            try:
                coerced = _coerce_value(raw_value, type(attr_value))
            except (ValueError, TypeError):
                raise FilterError(
                    expression,
                    f"Cannot compare attribute '{attr_name}' "
                    f"(type {type(attr_value).__name__}) with value '{raw_value}'",
                )
            try:
                if compare_fn(attr_value, coerced):
                    matching_ids.append(node.get_id())
            except TypeError:
                raise FilterError(
                    expression,
                    f"Operator '{comparator}' is not supported for "
                    f"attribute type {type(attr_value).__name__}",
                )

        return _to_concrete_subgraph(graph, matching_ids)

    # Compound helper
    def apply_operation(
        self,
        graph: Graph,
        op_type: str,
        query: str,
    ) -> ConcreteGraph:
        """Dispatch to search or filter based on op_type"""
        if op_type == "search":
            return self.search(graph, query)
        elif op_type == "filter":
            return self.filter(graph, query)
        else:
            raise ValueError(f"Unknown operation type: {op_type!r}")

# Internal helpers
def _parse_expression(expression: str):
    """Parse a filter expression and return (attr_name, comparator, raw_value)"""
    m = _FILTER_RE.match(expression)
    if not m:
        raise FilterError(
            expression,
            "Expression must be of the form '<attribute> <comparator> <value>' "
            "where comparator is one of: ==, !=, >, >=, <, <=",
        )
    return m.group(1), m.group(2), m.group(3)


def _coerce_value(raw: str, target_type: type) -> AttributeValue:
    """Coerce a raw string value to *target_type*"""
    if target_type is int:
        return int(raw)
    if target_type is float:
        return float(raw)
    if target_type is date:
        return date.fromisoformat(raw)
    # str – no coercion needed
    return raw


def _to_concrete_subgraph(graph: Graph, node_ids: List[str]) -> ConcreteGraph:
    """Build a ConcreteGraph subgraph from a list of node ids"""
    id_set = set(node_ids)
    sub = ConcreteGraph(directed=graph.is_directed())

    for nid in node_ids:
        node = graph.get_node_by_id(nid)
        if node is not None:
            from gviz_platform.graph import ConcreteNode
            concrete = ConcreteNode(node.get_id(), node.get_attributes())
            sub._nodes[concrete.get_id()] = concrete

    for edge in graph.get_edges():
        if edge.get_source_id() in id_set and edge.get_target_id() in id_set:
            from gviz_platform.graph import ConcreteEdge
            concrete_edge = ConcreteEdge(
                edge_id=edge.get_id(),
                source_id=edge.get_source_id(),
                target_id=edge.get_target_id(),
                directed=edge.is_directed(),
                attributes=edge.get_attributes(),
            )
            sub._edges[concrete_edge.get_id()] = concrete_edge

    return sub

# Comparator dispatch table
_COMPARE_FUNCTIONS: dict[str, Callable] = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">":  lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<":  lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
}
