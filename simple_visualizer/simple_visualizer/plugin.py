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
            "Renders a graph as a self-contained HTML page with an SVG-based "
            "node-link view and a node details panel."
        )

    def render(self, graph: Graph) -> str:
        payload = self._graph_to_payload(graph)
        payload_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
        graph_kind = "directed" if payload["directed"] else "undirected"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>gviz Simple Visualizer</title>
  <style>
    :root {{
      --bg-app: #0d1117;
      --bg-panel: #161b22;
      --bg-panel-alt: #1c2128;
      --bg-hover: #21262d;
      --border: #30363d;
      --border-bright: #444c56;
      --accent: #58a6ff;
      --accent-dim: rgba(88, 166, 255, 0.15);
      --accent-green: #3fb950;
      --accent-orange: #d29922;
      --text-primary: #e6edf3;
      --text-secondary: #8b949e;
      --text-muted: #484f58;
      --node-blue: #58a6ff;
      --node-purple: #bc8cff;
      --node-green: #3fb950;
      --node-orange: #e3b341;
      --node-cyan: #79c0ff;
      --node-selected: #f0883e;
      --edge-color: #444c56;
      --shadow: 0 24px 60px rgba(0, 0, 0, 0.28);
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      min-height: 100vh;
      font-family: Inter, system-ui, sans-serif;
      color: var(--text-primary);
      background:
        radial-gradient(circle at top left, rgba(88, 166, 255, 0.12), transparent 28%),
        radial-gradient(circle at bottom right, rgba(188, 140, 255, 0.08), transparent 24%),
        var(--bg-app);
    }}

    .page {{
      min-height: 100vh;
      padding: 24px 20px;
    }}

    .frame {{
      display: grid;
      grid-template-columns: minmax(0, 1.9fr) minmax(280px, 0.85fr);
      gap: 18px;
      max-width: 1460px;
      margin: 0 auto;
    }}

    .panel {{
      background: linear-gradient(180deg, rgba(28, 33, 40, 0.98), rgba(22, 27, 34, 0.98));
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }}

    .hero,
    .sidebar {{
      padding: 22px 24px;
    }}

    .eyebrow {{
      margin: 0 0 8px;
      font-size: 11px;
      font-weight: 700;
      line-height: 1.2;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      color: var(--accent);
    }}

    h1 {{
      margin: 0;
      font-size: 30px;
      line-height: 1.05;
      letter-spacing: -0.03em;
    }}

    .sub {{
      margin: 10px 0 0;
      color: var(--text-secondary);
      font-size: 14px;
      line-height: 1.5;
    }}

    .stats {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      padding: 0 24px 18px;
    }}

    .stat {{
      padding: 9px 13px;
      border-radius: 999px;
      border: 1px solid var(--border-bright);
      background: var(--bg-hover);
      color: var(--text-secondary);
      font-size: 12px;
      font-weight: 600;
      line-height: 1;
    }}

    .canvas-wrap {{
      position: relative;
      padding: 0 18px 18px;
    }}

    svg {{
      display: block;
      width: 100%;
      height: min(76vh, 820px);
      background:
        linear-gradient(rgba(68, 76, 86, 0.2) 1px, transparent 1px),
        linear-gradient(90deg, rgba(68, 76, 86, 0.2) 1px, transparent 1px),
        linear-gradient(180deg, #121820 0%, #0d1117 100%);
      background-size: 26px 26px, 26px 26px, auto;
      border-radius: 16px;
      border: 1px solid var(--border);
    }}

    .canvas-toolbar {{
      position: absolute;
      top: 16px;
      right: 34px;
      display: flex;
      gap: 8px;
    }}

    .zoom-btn {{
      width: 34px;
      height: 34px;
      border: 1px solid var(--border-bright);
      border-radius: 10px;
      background: rgba(22, 27, 34, 0.88);
      color: var(--text-primary);
      font-size: 18px;
      line-height: 1;
      cursor: pointer;
    }}

    .zoom-btn:hover {{
      background: var(--bg-hover);
      border-color: var(--accent);
    }}

    .sidebar h2 {{
      margin: 0 0 12px;
      font-size: 22px;
    }}

    .sidebar p {{
      margin: 0 0 18px;
      color: var(--text-secondary);
      font-size: 14px;
      line-height: 1.5;
    }}

    .detail-card {{
      border: 1px solid var(--border);
      border-radius: 16px;
      background: var(--bg-panel-alt);
      padding: 16px;
      min-height: 200px;
    }}

    .detail-id {{
      margin: 0 0 8px;
      font-size: 16px;
      font-weight: 700;
      line-height: 1.3;
    }}

    .detail-empty {{
      margin: 0;
      color: var(--text-secondary);
      font-size: 14px;
      line-height: 1.5;
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
      border-top: 1px solid var(--border);
    }}

    .attr-key {{
      font-size: 11px;
      font-weight: 700;
      line-height: 1.2;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-secondary);
    }}

    .attr-value {{
      font-size: 15px;
      line-height: 1.4;
      word-break: break-word;
    }}

    .edge {{
      stroke: var(--edge-color);
      stroke-width: 1.5;
      stroke-opacity: 0.74;
    }}

    .node {{
      fill-opacity: 0.18;
      stroke-width: 2.5;
      cursor: pointer;
      transition: fill-opacity 120ms ease, stroke-width 120ms ease;
    }}

    .node.is-active {{
      fill: rgba(240, 136, 62, 0.18);
      fill-opacity: 1;
      stroke: var(--node-selected);
      stroke-width: 3.6;
    }}

    .label {{
      font-size: 12px;
      font-weight: 600;
      line-height: 1;
      fill: var(--text-primary);
      text-anchor: middle;
      pointer-events: none;
    }}

    .caption {{
      font-size: 11px;
      font-weight: 500;
      line-height: 1;
      fill: var(--text-secondary);
      text-anchor: middle;
      pointer-events: none;
    }}

    .legend {{
      margin-top: 18px;
      display: grid;
      gap: 10px;
    }}

    .legend-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--text-secondary);
      font-size: 13px;
    }}

    .legend-swatch {{
      width: 12px;
      height: 12px;
      border-radius: 999px;
      border: 2px solid transparent;
    }}

    @media (max-width: 980px) {{
      .frame {{
        grid-template-columns: 1fr;
      }}

      svg {{
        height: 60vh;
      }}

      .canvas-toolbar {{
        right: 28px;
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
          <div class="stat">{graph_kind}</div>
          <div class="stat">D3 force layout</div>
          <div class="stat">drag enabled</div>
          <div class="stat">hover details</div>
        </div>
        <div class="canvas-wrap">
          <div class="canvas-toolbar">
            <button class="zoom-btn" id="zoom-in" type="button">+</button>
            <button class="zoom-btn" id="zoom-fit" type="button">⊡</button>
            <button class="zoom-btn" id="zoom-out" type="button">−</button>
          </div>
          <svg id="graph" viewBox="0 0 960 720" preserveAspectRatio="xMidYMid meet"></svg>
        </div>
      </section>
      <aside class="panel sidebar">
        <h2>Node details</h2>
        <p>Pan, zoom and drag nodes in the main view. Hover for quick details, click to keep a node selected.</p>
        <div class="detail-card" id="details">
          <p class="detail-empty">No node selected.</p>
        </div>
        <div class="legend">
          <div class="legend-row"><span class="legend-swatch" style="background: rgba(88, 166, 255, 0.18); border-color: #58a6ff;"></span> default node</div>
          <div class="legend-row"><span class="legend-swatch" style="background: rgba(240, 136, 62, 0.18); border-color: #f0883e;"></span> selected node</div>
        </div>
      </aside>
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
  <script>
    const graph = {payload_json};
    const svg = document.getElementById("graph");
    const details = document.getElementById("details");
    const svgSelection = d3.select(svg);
    const width = 960;
    const height = 720;
    const palette = ["#58a6ff", "#bc8cff", "#3fb950", "#e3b341", "#79c0ff"];
    const nodes = graph.nodes.map((node, index) => ({{
      ...node,
      color: palette[index % palette.length],
    }}));
    const links = graph.edges.map(edge => ({{ ...edge }}));
    const root = svgSelection.append("g").attr("class", "viewport");
    const edgesLayer = root.append("g").attr("class", "edges");
    const nodesLayer = root.append("g").attr("class", "nodes");
    let activeNodeId = null;
    let hoveredNodeId = null;

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

    function applySelection() {{
      nodeSelection
        .classed("is-selected", node => node.id === activeNodeId)
        .select("circle")
        .classed("is-active", node => node.id === activeNodeId || node.id === hoveredNodeId);
    }}

    function syncDetailsPanel() {{
      const node =
        nodes.find(candidate => candidate.id === hoveredNodeId) ||
        nodes.find(candidate => candidate.id === activeNodeId);

      if (node) {{
        renderDetails(node);
        return;
      }}

      details.innerHTML = '<p class="detail-empty">No node selected.</p>';
    }}

    const zoom = d3.zoom()
      .scaleExtent([0.25, 4])
      .on("zoom", event => {{
        root.attr("transform", event.transform);
      }});

    svgSelection.call(zoom);

    const linkSelection = edgesLayer
      .selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("class", "edge");

    const nodeSelection = nodesLayer
      .selectAll("g")
      .data(nodes)
      .enter()
      .append("g")
      .style("cursor", "pointer")
      .call(
        d3.drag()
          .on("start", dragStarted)
          .on("drag", dragged)
          .on("end", dragEnded)
      )
      .on("mouseover", (_, node) => {{
        hoveredNodeId = node.id;
        applySelection();
        syncDetailsPanel();
      }})
      .on("mouseout", (_, node) => {{
        if (hoveredNodeId === node.id) {{
          hoveredNodeId = null;
        }}
        applySelection();
        syncDetailsPanel();
      }})
      .on("click", (_, node) => {{
        activeNodeId = node.id;
        applySelection();
        syncDetailsPanel();
      }});

    nodeSelection
      .append("circle")
      .attr("class", "node")
      .attr("r", 18)
      .attr("fill", node => node.color)
      .attr("stroke", node => node.color);

    nodeSelection
      .append("text")
      .attr("class", "label")
      .attr("y", 4)
      .text(node => (node.label || node.id).slice(0, 14));

    nodeSelection
      .append("text")
      .attr("class", "caption")
      .attr("y", 30)
      .text(node => node.id);

    const simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id(node => node.id).distance(84).strength(0.45))
      .force("charge", d3.forceManyBody().strength(-260))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(34));

    function dragStarted(event, node) {{
      if (!event.active) {{
        simulation.alphaTarget(0.22).restart();
      }}
      node.fx = node.x;
      node.fy = node.y;
    }}

    function dragged(event, node) {{
      node.fx = event.x;
      node.fy = event.y;
    }}

    function dragEnded(event, node) {{
      if (!event.active) {{
        simulation.alphaTarget(0);
      }}
      node.fx = null;
      node.fy = null;
    }}

    simulation.on("tick", () => {{
      linkSelection
        .attr("x1", link => link.source.x)
        .attr("y1", link => link.source.y)
        .attr("x2", link => link.target.x)
        .attr("y2", link => link.target.y);

      nodeSelection.attr("transform", node => `translate(${{node.x}}, ${{node.y}})`);
    }});

    function fitGraph() {{
      const bounds = root.node().getBBox();
      if (!bounds.width || !bounds.height) {{
        svgSelection.call(
          zoom.transform,
          d3.zoomIdentity.translate(width / 2, height / 2).scale(1)
        );
        return;
      }}

      const scale = Math.max(
        0.25,
        Math.min(2.2, 0.88 / Math.max(bounds.width / width, bounds.height / height))
      );
      const translateX = width / 2 - scale * (bounds.x + bounds.width / 2);
      const translateY = height / 2 - scale * (bounds.y + bounds.height / 2);

      svgSelection
        .transition()
        .duration(350)
        .call(zoom.transform, d3.zoomIdentity.translate(translateX, translateY).scale(scale));
    }}

    document.getElementById("zoom-in").addEventListener("click", () => {{
      svgSelection.transition().duration(180).call(zoom.scaleBy, 1.25);
    }});

    document.getElementById("zoom-out").addEventListener("click", () => {{
      svgSelection.transition().duration(180).call(zoom.scaleBy, 0.8);
    }});

    document.getElementById("zoom-fit").addEventListener("click", () => {{
      fitGraph();
    }});

    setTimeout(fitGraph, 260);
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
