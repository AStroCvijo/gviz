# JSON-to-graph parser

from __future__ import annotations

import json
import re
import uuid
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from api.exceptions import ParseError
from api.models import AttributeValue
from gviz_platform.graph import ConcreteEdge, ConcreteGraph, ConcreteNode


# ISO date pattern (YYYY-MM-DD)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class JSONParser:
    """Parse a JSON document and produce a ConcreteGraph"""

    def __init__(self, directed: bool = True) -> None:
        self._directed = directed
        self._graph: ConcreteGraph = ConcreteGraph(directed=directed)
        self._known_ids: Set[str] = set()       # all @id values in the doc
        self._edge_counter: int = 0

    # Public interface
    def parse_file(self, file_path: str, directed: bool = True) -> ConcreteGraph:
        """Parse a JSON file and return a graph"""
        path = Path(file_path)
        if not path.exists():
            raise ParseError(str(file_path), "File does not exist")
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ParseError(str(file_path), f"Invalid JSON: {exc}") from exc
        except OSError as exc:
            raise ParseError(str(file_path), str(exc)) from exc

        return self._build_graph(data, directed=directed)

    def parse_string(self, json_string: str, directed: bool = True) -> ConcreteGraph:
        """Parse a JSON string and return a graph"""
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as exc:
            raise ParseError("<string>", f"Invalid JSON: {exc}") from exc

        return self._build_graph(data, directed=directed)

    # Two-pass graph construction
    def _build_graph(self, data: Any, directed: bool) -> ConcreteGraph:
        """Build and return a graph from raw parsed JSON data."""
        self._directed = directed
        self._graph = ConcreteGraph(directed=directed)
        self._known_ids = set()
        self._edge_counter = 0

        # Pass 1: collect all @id values
        self._collect_ids(data)

        # Pass 2: build nodes and edges
        self._process_value(data, parent_id=None, edge_label=None)

        return self._graph

    def _collect_ids(self, data: Any) -> None:
        """Recursively collect all ``@id`` values in the document."""
        if isinstance(data, dict):
            if "@id" in data:
                self._known_ids.add(str(data["@id"]))
            for value in data.values():
                self._collect_ids(value)
        elif isinstance(data, list):
            for item in data:
                self._collect_ids(item)

    # Recursive processing (pass 2)
    def _process_value(
        self,
        value: Any,
        parent_id: Optional[str],
        edge_label: Optional[str],
    ) -> Optional[str]:
        """Process a JSON value recursively"""
        if isinstance(value, dict):
            return self._process_object(value, parent_id, edge_label)
        elif isinstance(value, list):
            self._process_array(value, parent_id, edge_label)
            return None
        elif isinstance(value, str) and value in self._known_ids:
            # String that matches an @id → reference edge
            if parent_id is not None:
                self._add_edge(parent_id, value, label=edge_label or "ref")
            return None
        else:
            # Scalar — handled as attribute by the caller
            return None

    def _process_object(
        self,
        obj: dict,
        parent_id: Optional[str],
        edge_label: Optional[str],
    ) -> str:
        """Turn a JSON object into a node and process its children."""
        node_id = str(obj.get("@id", uuid.uuid4()))
        attributes: Dict[str, AttributeValue] = {}

        for key, val in obj.items():
            if key == "@id":
                continue
            if isinstance(val, dict):
                child_id = self._process_object(val, parent_id=node_id, edge_label=key)
            elif isinstance(val, list):
                self._process_array(val, parent_id=node_id, edge_label=key)
            elif isinstance(val, str) and val in self._known_ids:
                # Reference to another node
                self._add_edge(node_id, val, label=key)
            else:
                # Scalar attribute
                typed = _infer_type(val)
                if typed is not None:
                    attributes[key] = typed

        node = ConcreteNode(node_id=node_id, attributes=attributes)
        self._graph.add_or_update_node(node)

        if parent_id is not None:
            self._add_edge(parent_id, node_id, label=edge_label or "child")

        return node_id

    def _process_array(
        self,
        arr: list,
        parent_id: Optional[str],
        edge_label: Optional[str],
    ) -> None:
        """Process a JSON array, creating edges for each resolvable element."""
        scalar_parts: List[str] = []

        for item in arr:
            if isinstance(item, dict):
                self._process_object(item, parent_id=parent_id, edge_label=edge_label)
            elif isinstance(item, str) and item in self._known_ids:
                if parent_id is not None:
                    self._add_edge(parent_id, item, label=edge_label or "ref")
            else:
                typed = _infer_type(item)
                if typed is not None:
                    scalar_parts.append(str(typed))

        # Scalar array elements are stored as a comma-joined attribute on the
        # parent node, if there is one.
        if scalar_parts and parent_id is not None:
            node = self._graph.get_node_by_id(parent_id)
            if node is not None and edge_label:
                node.set_attribute(edge_label, ", ".join(scalar_parts))

    # Edge helpers
    def _add_edge(self, source_id: str, target_id: str, label: str) -> None:
        """Create and add a directed edge if both nodes are (or will be) present."""
        if source_id == target_id:
            pass
        self._edge_counter += 1
        edge_id = f"e{self._edge_counter}"
        # Use loose add: at this point the target node may not yet exist in the graph
        edge = ConcreteEdge(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            directed=self._directed,
            attributes={"label": label} if label else {},
        )
        try:
            self._graph.add_edge_loose(edge)
        except ValueError:
            # Duplicate edge id – should not happen, but guard anyway
            pass


# Type inference helper
def _infer_type(value: Any) -> Optional[AttributeValue]:
    """Convert a raw JSON scalar to an AttributeValue"""
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    if isinstance(value, str):
        if _DATE_RE.match(value):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        return value
    # Fallback for unexpected types
    return str(value)
