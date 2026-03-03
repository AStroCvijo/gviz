from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict

from api.models import Edge, Graph, Node
from api.plugins import VisualizerPlugin


class SimpleVisualizerPlugin(VisualizerPlugin):
    """Render a graph as a lightweight self-contained HTML view."""

    def get_name(self) -> str:
        return "simple-visualizer"

    def get_description(self) -> str:
        return (
            "Provides graph data for the existing gviz UI shell so the "
            "standard main view can render a real graph instead of mock data."
        )

    def render(self, graph: Graph) -> str:
        payload = self._graph_to_payload(graph)
        payload_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
        return (
            "<script>"
            f"window.GVIZ_PLUGIN_BOOTSTRAP={{visualizerName:'simple-visualizer',graph:{payload_json}}};"
            "</script>"
        )

    def _graph_to_payload(self, graph: Graph) -> Dict[str, Any]:
        nodes = [self._node_to_dict(node) for node in graph.get_nodes()]
        edges = [self._edge_to_dict(edge) for edge in graph.get_edges()]
        return {
            "directed": graph.is_directed(),
            "nodes": nodes,
            "edges": edges,
        }

    def _node_to_dict(self, node: Node) -> Dict[str, Any]:
        attrs = {
            key: self._serialize_value(value)
            for key, value in node.get_attributes().items()
        }
        return {
            "id": node.get_id(),
            "label": self._node_label(node),
            "attrs": attrs,
        }

    def _edge_to_dict(self, edge: Edge) -> Dict[str, Any]:
        return {
            "id": edge.get_id(),
            "source": edge.get_source_id(),
            "target": edge.get_target_id(),
            "directed": edge.is_directed(),
            "attributes": {
                key: self._serialize_value(value)
                for key, value in edge.get_attributes().items()
            },
        }

    def _node_label(self, node: Node) -> str:
        attrs = node.get_attributes()
        for candidate in ("name", "title", "label"):
            value = attrs.get(candidate)
            if value is not None:
                return str(value)
        return node.get_id()

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, (int, float, str)):
            return value
        if isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return {
                str(key): self._serialize_value(item)
                for key, item in value.items()
            }
        return str(value)
