from __future__ import annotations

import re
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import date
from typing import Any, Dict, List, Optional, Set
from xml.dom import minidom

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


class XMLWriter:

    def __init__(self, root_tag: str = "graph") -> None:
        self._root_tag = root_tag

    def write_string(self, graph: ConcreteGraph) -> str:
        children = self._build_children_map(graph)
        root_ids = self._find_roots(graph, children)

        root = ET.Element(self._root_tag, directed=str(graph.is_directed()).lower())
        visited: Set[str] = set()

        for node_id in root_ids:
            self._write_node(graph, node_id, root, children, visited)

        for node in graph.get_nodes():
            if node.get_id() not in visited:
                self._write_node(graph, node.get_id(), root, children, visited)

        rough = ET.tostring(root, encoding="unicode")
        return minidom.parseString(rough).toprettyxml(indent="  ")

    def write_file(self, graph: ConcreteGraph, file_path: str) -> None:
        xml_string = self.write_string(graph)
        Path(file_path).write_text(xml_string, encoding="utf-8")

    def _build_children_map(self, graph: ConcreteGraph) -> Dict[str, List[ConcreteEdge]]:
        children: Dict[str, List[ConcreteEdge]] = {}
        for node in graph.get_nodes():
            children[node.get_id()] = []
        for edge in graph.get_edges():
            src = edge.get_source_id()
            if src in children:
                children[src].append(edge)
        return children

    def _find_roots(self, graph: ConcreteGraph, children: Dict[str, List[ConcreteEdge]]) -> List[str]:
        has_parent: Set[str] = set()
        for edge in graph.get_edges():
            has_parent.add(edge.get_target_id())
        roots = [n.get_id() for n in graph.get_nodes() if n.get_id() not in has_parent]
        if not roots:
            roots = [graph.get_nodes()[0].get_id()] if graph.get_nodes() else []
        return roots

    def _write_node(
        self,
        graph: ConcreteGraph,
        node_id: str,
        parent_el: ET.Element,
        children: Dict[str, List[ConcreteEdge]],
        visited: Set[str],
    ) -> None:
        node = graph.get_node_by_id(node_id)
        if node is None:
            return

        if node_id in visited:
            ET.SubElement(parent_el, "ref", ref=node_id)
            return

        visited.add(node_id)

        attrs = node.get_attributes()
        tag = str(attrs.get("tag", "node"))
        xml_attrs: Dict[str, str] = {"id": node_id}

        for key, value in attrs.items():
            if key == "tag":
                continue
            xml_attrs[key] = _serialize_attr(value)

        el = ET.SubElement(parent_el, tag, attrib=xml_attrs)

        for edge in children.get(node_id, []):
            target_id = edge.get_target_id()
            self._write_node(graph, target_id, el, children, visited)


def _serialize_attr(value: AttributeValue) -> str:
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


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
