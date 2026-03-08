from __future__ import annotations

import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import date
from typing import Any, Dict, Optional, Set

from api.exceptions import ParseError
from api.models import AttributeValue
from gviz_platform.graph import ConcreteEdge, ConcreteGraph, ConcreteNode


class XMLParser:

    def __init__(self, directed: bool = True) -> None:
        self._directed = directed
        self._graph: ConcreteGraph = ConcreteGraph(directed=directed)
        self._known_ids: Set[str] = set()
        self._edge_counter: int = 0

    def parse_file(self, file_path: str, directed: bool = True) -> ConcreteGraph:
        path = Path(file_path)
        if not path.exists():
            raise ParseError(str(file_path), "File does not exist")
        try:
            tree = ET.parse(str(path))
            root = tree.getroot()
        except ET.ParseError as exc:
            raise ParseError(str(file_path), f"Invalid XML: {exc}") from exc
        except OSError as exc:
            raise ParseError(str(file_path), str(exc)) from exc

        return self._build_graph(root, directed=directed)

    def parse_string(self, xml_string: str, directed: bool = True) -> ConcreteGraph:
        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as exc:
            raise ParseError("<string>", f"Invalid XML: {exc}") from exc

        return self._build_graph(root, directed=directed)

    def _build_graph(self, root: ET.Element, directed: bool) -> ConcreteGraph:
        self._directed = directed
        self._graph = ConcreteGraph(directed=directed)
        self._known_ids = set()
        self._edge_counter = 0

        self._collect_ids(root)
        self._process_element(root, parent_id=None)

        return self._graph

    def _collect_ids(self, element: ET.Element) -> None:
        elem_id = element.get("id")
        if elem_id is not None:
            self._known_ids.add(elem_id)
        for child in element:
            self._collect_ids(child)

    def _process_element(self, element: ET.Element, parent_id: Optional[str]) -> str:
        node_id = element.get("id") or str(uuid.uuid4())

        ref_target = element.get("ref")
        if ref_target and ref_target in self._known_ids:
            if parent_id is not None:
                label = element.get("label") or element.tag or "ref"
                self._add_edge(parent_id, ref_target, label=label)
            return ref_target

        attributes: Dict[str, AttributeValue] = {}
        attributes["tag"] = element.tag

        for attr_name, attr_value in element.attrib.items():
            if attr_name in ("id", "ref"):
                continue
            typed = _infer_type(attr_value)
            if typed is not None:
                attributes[attr_name] = typed

        text = (element.text or "").strip()
        if text and not len(element):
            typed = _infer_type(text)
            if typed is not None:
                attributes["text"] = typed

        node = ConcreteNode(node_id=node_id, attributes=attributes)
        self._graph.add_or_update_node(node)

        if parent_id is not None:
            label = element.get("label") or element.tag or "child"
            self._add_edge(parent_id, node_id, label=label)

        for child in element:
            self._process_element(child, parent_id=node_id)

        return node_id

    def _add_edge(self, source_id: str, target_id: str, label: str) -> None:
        self._edge_counter += 1
        edge_id = f"e{self._edge_counter}"
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
            pass


_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _infer_type(value: Any) -> Optional[AttributeValue]:
    if value is None:
        return None
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        if _DATE_RE.match(value):
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        return value
    return str(value)
