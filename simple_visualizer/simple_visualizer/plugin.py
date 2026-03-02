from __future__ import annotations

import html
import json
from datetime import date
from typing import Any, Dict, List

from api.models import Edge, Graph, Node
from api.plugins import VisualizerPlugin


class SimpleVisualizerPlugin(VisualizerPlugin):
    """Render a graph as a lightweight self-contained HTML view."""

    def get_name(self) -> str:
        return "simple-visualizer"

    def get_description(self) -> str:
        return (
            "Renders a graph as a self-contained HTML page with an SVG-based "
            "node-link view and a node details panel."
        )

    def render(self, graph: Graph) -> str:
        payload = self._graph_to_payload(graph)
        payload_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
        title = html.escape(
            f"Simple Visualizer ({len(payload['nodes'])} nodes, "
            f"{len(payload['edges'])} edges)"
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4efe6;
      --panel: #fffaf2;
      --ink: #1e2430;
      --muted: #6a7280;
      --line: #d9cfbf;
      --accent: #156f6a;
      --accent-soft: #d7efe9;
      --node: #d97706;
      --node-soft: rgba(217, 119, 6, 0.18);
      --shadow: 0 18px 50px rgba(30, 36, 48, 0.08);
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #fff8eb 0%, var(--bg) 45%),
        linear-gradient(135deg, #efe7da 0%, #f7f3eb 100%);
    }}

    .page {{
      min-height: 100vh;
      padding: 24px;
    }}

    .frame {{
      display: grid;
      grid-template-columns: minmax(0, 2.3fr) minmax(260px, 0.9fr);
      gap: 20px;
      max-width: 1400px;
      margin: 0 auto;
    }}

    .panel {{
      background: rgba(255, 250, 242, 0.9);
      border: 1px solid rgba(217, 207, 191, 0.85);
      border-radius: 22px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(6px);
    }}

    .hero {{
      padding: 22px 24px 0;
    }}

    .eyebrow {{
      margin: 0 0 8px;
      font: 700 11px/1.2 Arial, sans-serif;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--accent);
    }}

    h1 {{
      margin: 0;
      font-size: 32px;
      line-height: 1.05;
    }}

    .sub {{
      margin: 10px 0 0;
      color: var(--muted);
      font: 400 14px/1.5 Arial, sans-serif;
    }}

    .stats {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      padding: 18px 24px 0;
    }}

    .stat {{
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #fffdf9;
      font: 600 12px/1 Arial, sans-serif;
      color: var(--muted);
    }}

    .canvas-wrap {{
      padding: 18px 18px 18px;
    }}

    svg {{
      display: block;
      width: 100%;
      height: min(72vh, 760px);
      background:
        linear-gradient(rgba(217, 207, 191, 0.28) 1px, transparent 1px),
        linear-gradient(90deg, rgba(217, 207, 191, 0.28) 1px, transparent 1px),
        linear-gradient(180deg, #fffdf8 0%, #fbf6ee 100%);
      background-size: 28px 28px, 28px 28px, auto;
      border-radius: 18px;
      border: 1px solid var(--line);
    }}

    .sidebar {{
      padding: 24px;
    }}

    .sidebar h2 {{
      margin: 0 0 12px;
      font-size: 22px;
    }}

    .sidebar p {{
      margin: 0 0 18px;
      color: var(--muted);
      font: 400 14px/1.5 Arial, sans-serif;
    }}

    .detail-card {{
      border: 1px solid var(--line);
      border-radius: 18px;
      background: #fffdf9;
      padding: 16px;
      min-height: 200px;
    }}

    .detail-id {{
      margin: 0 0 8px;
      font: 700 16px/1.3 Arial, sans-serif;
    }}

    .detail-empty {{
      margin: 0;
      color: var(--muted);
      font: 400 14px/1.5 Arial, sans-serif;
    }}

    .attrs {{
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }}

    .attr {{
      display: grid;
      gap: 4px;
      padding-top: 10px;
      border-top: 1px solid #eee4d6;
    }}

    .attr-key {{
      font: 700 11px/1.2 Arial, sans-serif;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }}

    .attr-value {{
      font: 400 15px/1.4 Arial, sans-serif;
      word-break: break-word;
    }}

    .edge {{
      stroke: rgba(30, 36, 48, 0.32);
      stroke-width: 1.6;
    }}

    .node {{
      fill: var(--node-soft);
      stroke: var(--node);
      stroke-width: 2.6;
      cursor: pointer;
      transition: transform 120ms ease;
    }}

    .node.is-active {{
      fill: rgba(21, 111, 106, 0.18);
      stroke: var(--accent);
      stroke-width: 3.6;
    }}

    .label {{
      font: 600 12px/1 Arial, sans-serif;
      fill: var(--ink);
      text-anchor: middle;
      pointer-events: none;
    }}

    .caption {{
      font: 500 11px/1 Arial, sans-serif;
      fill: var(--muted);
      text-anchor: middle;
      pointer-events: none;
    }}

    @media (max-width: 980px) {{
      .frame {{
        grid-template-columns: 1fr;
      }}

      svg {{
        height: 60vh;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <div class="frame">
      <section class="panel">
        <div class="hero">
          <p class="eyebrow">gviz plugin</p>
          <h1>Simple graph view</h1>
          <p class="sub">A lightweight HTML renderer for quick graph inspection.</p>
        </div>
        <div class="stats">
          <div class="stat">{len(payload["nodes"])} nodes</div>
          <div class="stat">{len(payload["edges"])} edges</div>
          <div class="stat">{'directed' if payload["directed"] else 'undirected'}</div>
        </div>
        <div class="canvas-wrap">
          <svg id="graph" viewBox="0 0 960 720" preserveAspectRatio="xMidYMid meet"></svg>
        </div>
      </section>
      <aside class="panel sidebar">
        <h2>Node details</h2>
        <p>Click a node to inspect its attributes.</p>
        <div class="detail-card" id="details">
          <p class="detail-empty">No node selected.</p>
        </div>
      </aside>
    </div>
  </div>
  <script>
    const graph = {payload_json};
    const svg = document.getElementById("graph");
    const details = document.getElementById("details");
    const width = 960;
    const height = 720;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.34;

    const nodes = graph.nodes.map((node, index) => {{
      const angle = (Math.PI * 2 * index) / Math.max(graph.nodes.length, 1);
      return {{
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      }};
    }});

    const nodeById = new Map(nodes.map(node => [node.id, node]));

    graph.edges.forEach(edge => {{
      const source = nodeById.get(edge.source);
      const target = nodeById.get(edge.target);
      if (!source || !target) return;

      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", source.x);
      line.setAttribute("y1", source.y);
      line.setAttribute("x2", target.x);
      line.setAttribute("y2", target.y);
      line.setAttribute("class", "edge");
      svg.appendChild(line);
    }});

    let activeGroup = null;

    function renderDetails(node) {{
      const attrs = Object.entries(node.attributes || {{}});
      const attrsHtml = attrs.length
        ? `<div class="attrs">${{attrs.map(([key, value]) => `
            <div class="attr">
              <div class="attr-key">${{escapeHtml(key)}}</div>
              <div class="attr-value">${{escapeHtml(String(value))}}</div>
            </div>
          `).join("")}}</div>`
        : '<p class="detail-empty">This node has no attributes.</p>';

      details.innerHTML = `
        <p class="detail-id">${{escapeHtml(node.label)}}</p>
        <p class="detail-empty">Node id: ${{escapeHtml(node.id)}}</p>
        ${{attrsHtml}}
      `;
    }}

    function escapeHtml(value) {{
      return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
    }}

    nodes.forEach(node => {{
      const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
      group.setAttribute("transform", `translate(${{node.x}}, ${{node.y}})`);
      group.style.transformOrigin = `${{node.x}}px ${{node.y}}px`;

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("r", "22");
      circle.setAttribute("class", "node");

      const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
      label.setAttribute("class", "label");
      label.setAttribute("y", "4");
      label.textContent = (node.label || node.id).slice(0, 14);

      const caption = document.createElementNS("http://www.w3.org/2000/svg", "text");
      caption.setAttribute("class", "caption");
      caption.setAttribute("y", "40");
      caption.textContent = node.id;

      group.appendChild(circle);
      group.appendChild(label);
      group.appendChild(caption);

      group.addEventListener("click", () => {{
        if (activeGroup) {{
          activeGroup.querySelector("circle").classList.remove("is-active");
        }}
        activeGroup = group;
        circle.classList.add("is-active");
        renderDetails(node);
      }});

      svg.appendChild(group);
    }});
  </script>
</body>
</html>"""

    def _graph_to_payload(self, graph: Graph) -> Dict[str, Any]:
        nodes = [self._node_to_dict(node) for node in graph.get_nodes()]
        edges = [self._edge_to_dict(edge) for edge in graph.get_edges()]
        return {
            "directed": graph.is_directed(),
            "nodes": nodes,
            "edges": edges,
        }

    def _node_to_dict(self, node: Node) -> Dict[str, Any]:
        attributes = {
            key: self._serialize_value(value)
            for key, value in node.get_attributes().items()
        }
        return {
            "id": node.get_id(),
            "label": self._node_label(node),
            "attributes": attributes,
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
