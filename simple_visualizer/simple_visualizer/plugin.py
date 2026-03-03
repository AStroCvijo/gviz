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
  <link rel="stylesheet" href="gviz/app/static/app/css/main.css">
</head>
<body>
<div class="app-layout">
  <header class="topbar">
    <div class="topbar-logo">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="5" cy="12" r="3"></circle>
        <circle cx="19" cy="5" r="3"></circle>
        <circle cx="19" cy="19" r="3"></circle>
        <line x1="7.5" y1="10.5" x2="17" y2="6.5"></line>
        <line x1="7.5" y1="13.5" x2="17" y2="17.5"></line>
      </svg>
      gviz
    </div>
    <div class="workspace-tabs">
      <div class="ws-tab active">
        <span class="ws-dot"></span>
        Simple Visualizer Preview
        <span class="ws-close">✕</span>
      </div>
    </div>
    <div class="topbar-actions">
      <button class="btn btn-ghost" type="button">Plugin Preview</button>
    </div>
  </header>

  <div class="toolbar">
    <div class="toolbar-group">
      <div class="plugin-select-wrap">
        <span class="select-icon">⬡</span>
        <select class="plugin-select" disabled>
          <option selected>Simple Visualizer</option>
        </select>
        <span class="select-arrow">▾</span>
      </div>
    </div>
    <div class="toolbar-divider"></div>
    <div class="toolbar-group">
      <span style="color:var(--text-muted);font-size:11px">View:</span>
      <div class="viz-toggle">
        <button class="viz-toggle-btn active" type="button">Simple</button>
      </div>
    </div>
    <div class="toolbar-divider"></div>
    <div class="toolbar-group">
      <div class="search-wrap">
        <span class="search-icon">🔍</span>
        <input type="text" class="search-input" placeholder="Search nodes…" id="search-input">
      </div>
      <button class="btn btn-ghost" type="button" id="btn-search">Search</button>
    </div>
    <div class="toolbar-divider"></div>
    <div class="toolbar-group">
      <div class="filter-wrap">
        <span class="filter-icon">⚡</span>
        <input type="text" class="filter-input" placeholder="age > 25" id="filter-input">
      </div>
      <button class="btn btn-ghost" type="button" id="btn-filter">Filter</button>
      <button class="btn btn-ghost" type="button" id="btn-reset">↺ Reset</button>
    </div>
  </div>

  <div class="main-content">
    <div class="panel panel-tree" id="panel-tree">
      <div class="panel-header">
        <span class="panel-title">Tree View</span>
      </div>
      <div class="panel-body" id="tree-body"></div>
    </div>

    <div class="panel panel-main">
      <div class="graph-stats">
        <div class="stat-badge">
          <span class="stat-dot"></span>
          {len(payload["nodes"])} nodes
        </div>
        <div class="stat-badge">
          <span class="stat-dot edge-dot"></span>
          {len(payload["edges"])} edges
        </div>
        <div class="stat-badge" style="color:var(--accent-orange)">
          {graph_kind}
        </div>
      </div>
      <svg id="graph-canvas"></svg>
      <div class="canvas-overlay hidden" id="canvas-overlay">
        <div class="canvas-overlay-icon">gviz</div>
        <div class="canvas-overlay-text">No graph loaded</div>
      </div>
      <div class="zoom-controls">
        <button class="zoom-btn" id="zoom-in" title="Zoom in" type="button">+</button>
        <button class="zoom-btn" id="zoom-fit" title="Fit to screen" type="button">⊡</button>
        <button class="zoom-btn" id="zoom-out" title="Zoom out" type="button">−</button>
      </div>
    </div>

    <div class="panel panel-right">
      <div class="bird-view-container">
        <div class="panel-header">
          <span class="panel-title">Bird View</span>
        </div>
        <canvas id="bird-view-canvas"></canvas>
      </div>
      <div class="node-details-container">
        <div class="panel-header">
          <span class="panel-title">Node Details</span>
        </div>
        <div class="node-details-body" id="node-details-body">
          <div class="detail-empty">Hover or click a node</div>
        </div>
      </div>
    </div>
  </div>

  <div class="terminal-panel">
    <div class="terminal-header">
      <div class="terminal-title">
        <span class="terminal-dot"></span>
        Terminal
      </div>
    </div>
    <div class="terminal-output" id="term-output"></div>
    <div class="terminal-input-row">
      <span class="term-prompt-label">gviz&gt;</span>
      <input type="text" class="term-input" value="simple visualizer preview ready" readonly>
    </div>
  </div>
</div>
  <script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
  <script>
    const graph = {payload_json};
    const svg = document.getElementById("graph-canvas");
    const treeBody = document.getElementById("tree-body");
    const birdCanvas = document.getElementById("bird-view-canvas");
    const details = document.getElementById("node-details-body");
    const termOutput = document.getElementById("term-output");
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
    let birdPositions = [];

    function renderDetails(node) {{
      const attrs = Object.entries(node.attributes || {{}});
      let html = `
        <div class="detail-node-id">
          <span class="node-color-dot"></span>
          <span class="node-id-text">${{escapeHtml(node.id)}}</span>
        </div>
        <div class="detail-divider"></div>
      `;

      if (!attrs.length) {{
        html += '<div class="detail-empty">This node has no attributes.</div>';
      }}

      attrs.forEach(([key, value]) => {{
        html += `
          <div class="detail-row">
            <span class="detail-key">${{escapeHtml(key)}}</span>
            <span class="detail-val">${{escapeHtml(String(value))}}</span>
          </div>
        `;
      }});

      details.innerHTML = html;
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

      treeBody.querySelectorAll(".tree-node-row").forEach(row => {{
        const selected = row.dataset.nodeId === activeNodeId;
        row.classList.toggle("selected", selected);
        if (selected) {{
          row.scrollIntoView({{ block: "nearest" }});
        }}
      }});

      drawBirdView();
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

    function termPrint(text, cls) {{
      const line = document.createElement("div");
      line.className = `term-line ${{cls || ""}}`;
      line.textContent = text;
      termOutput.appendChild(line);
      termOutput.scrollTop = termOutput.scrollHeight;
    }}

    function selectNode(nodeId) {{
      activeNodeId = nodeId;
      applySelection();
      syncDetailsPanel();
      termPrint(`select --node=${{nodeId}}`, "cmd");
    }}

    const zoom = d3.zoom()
      .scaleExtent([0.25, 4])
      .on("zoom", event => {{
        root.attr("transform", event.transform);
        drawBirdView();
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
        selectNode(node.id);
      }});

    nodeSelection
      .append("circle")
      .attr("class", "node")
      .attr("r", 18)
      .attr("fill", node => node.color)
      .attr("stroke", node => node.color)
      .style("fill-opacity", 0.2);

    nodeSelection
      .append("text")
      .attr("class", "label")
      .attr("dy", 26)
      .style("fill", "#8b949e")
      .text(node => (node.label || node.id).split(" ")[0].slice(0, 14));

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
      drawBirdView();
    }});

    function renderTree() {{
      if (!nodes.length) {{
        treeBody.innerHTML = '<p class="detail-empty">No graph loaded.</p>';
        return;
      }}

      const rootNode = nodes[0];
      const nodeMap = new Map(nodes.map(node => [node.id, node]));
      const childrenById = new Map();

      links.forEach(link => {{
        const sourceId = link.source.id || link.source;
        const targetId = link.target.id || link.target;
        if (!childrenById.has(sourceId)) {{
          childrenById.set(sourceId, []);
        }}
        childrenById.get(sourceId).push(targetId);
      }});

      function buildNode(node, depth, path) {{
        const childIds = childrenById.get(node.id) || [];
        const hasChildren = childIds.length > 0;

        const wrap = document.createElement("div");
        const row = document.createElement("div");
        row.className = "tree-node-row";
        row.dataset.nodeId = node.id;
        row.style.paddingLeft = `${{8 + depth * 16}}px`;
        row.innerHTML = `
          <span class="tree-toggle ${{hasChildren ? "" : "leaf"}}" data-toggle>${{hasChildren ? "▶" : ""}}</span>
          <span class="tree-icon">●</span>
          <span class="tree-label">${{escapeHtml(node.label)}}</span>
          ${{hasChildren ? `<span class="tree-badge">${{childIds.length}}</span>` : ""}}
        `;

        const childrenDiv = document.createElement("div");
        childrenDiv.className = "tree-children";
        let populated = false;

        function populateChildren() {{
          if (populated || !hasChildren) return;
          populated = true;

          childIds.forEach(childId => {{
            const child = nodeMap.get(childId);
            if (!child) return;

            if (path.has(childId)) {{
              const cycleRow = document.createElement("div");
              cycleRow.className = "tree-node-row";
              cycleRow.dataset.nodeId = childId;
              cycleRow.style.paddingLeft = `${{24 + (depth + 1) * 16}}px`;
              cycleRow.innerHTML = `
                <span class="tree-toggle leaf"></span>
                <span class="tree-icon" style="color: var(--accent-orange)">↩</span>
                <span class="tree-label">${{escapeHtml(child.label)}} (ref)</span>
              `;
              cycleRow.addEventListener("click", () => selectNode(childId));
              childrenDiv.appendChild(cycleRow);
              return;
            }}

            const nextPath = new Set(path);
            nextPath.add(childId);
            childrenDiv.appendChild(buildNode(child, depth + 1, nextPath));
          }});
        }}

        row.addEventListener("click", event => {{
          selectNode(node.id);

          if (!hasChildren) return;
          if (event.target.closest(".tree-badge") && !event.target.closest("[data-toggle]")) return;

          populateChildren();
          const open = childrenDiv.classList.toggle("open");
          const toggle = row.querySelector("[data-toggle]");
          if (toggle) {{
            toggle.textContent = open ? "▼" : "▶";
          }}
        }});

        wrap.appendChild(row);
        wrap.appendChild(childrenDiv);
        return wrap;
      }}

      treeBody.innerHTML = "";
      treeBody.appendChild(buildNode(rootNode, 0, new Set([rootNode.id])));
    }}

    function drawBirdView() {{
      const ctx = birdCanvas.getContext("2d");
      const widthPx = birdCanvas.clientWidth || 320;
      const heightPx = birdCanvas.clientHeight || 130;
      birdCanvas.width = widthPx;
      birdCanvas.height = heightPx;

      const positioned = nodes.filter(node => Number.isFinite(node.x) && Number.isFinite(node.y));
      ctx.clearRect(0, 0, widthPx, heightPx);
      ctx.fillStyle = "#0d1117";
      ctx.fillRect(0, 0, widthPx, heightPx);

      if (!positioned.length) {{
        birdPositions = [];
        return;
      }}

      const xs = positioned.map(node => node.x);
      const ys = positioned.map(node => node.y);
      const minX = Math.min(...xs) - 30;
      const maxX = Math.max(...xs) + 30;
      const minY = Math.min(...ys) - 30;
      const maxY = Math.max(...ys) + 30;
      const scale = Math.min(widthPx / Math.max(maxX - minX, 1), heightPx / Math.max(maxY - minY, 1)) * 0.88;
      const offsetX = (widthPx - (maxX - minX) * scale) / 2 - minX * scale;
      const offsetY = (heightPx - (maxY - minY) * scale) / 2 - minY * scale;

      birdPositions = positioned.map(node => ({{
        id: node.id,
        x: node.x * scale + offsetX,
        y: node.y * scale + offsetY,
        color: node.color,
      }}));
      const posMap = new Map(birdPositions.map(item => [item.id, item]));

      links.forEach(link => {{
        const sourceId = link.source.id || link.source;
        const targetId = link.target.id || link.target;
        const source = posMap.get(sourceId);
        const target = posMap.get(targetId);
        if (!source || !target) return;
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = "#30363d";
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }});

      birdPositions.forEach(node => {{
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.id === activeNodeId ? 5.8 : 4.1, 0, Math.PI * 2);
        ctx.fillStyle = node.id === activeNodeId ? "rgba(240, 136, 62, 0.28)" : `${{node.color}}55`;
        ctx.fill();
        ctx.strokeStyle = node.id === activeNodeId ? "#f0883e" : node.color;
        ctx.lineWidth = node.id === activeNodeId ? 1.6 : 1.1;
        ctx.stroke();
      }});
    }}

    birdCanvas.addEventListener("click", event => {{
      const rect = birdCanvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;
      const match = birdPositions.find(node => Math.hypot(node.x - x, node.y - y) <= 8);
      if (match) {{
        selectNode(match.id);
      }}
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

    document.getElementById("btn-reset").addEventListener("click", () => {{
      activeNodeId = null;
      hoveredNodeId = null;
      applySelection();
      syncDetailsPanel();
      termPrint("reset", "info");
    }});

    document.getElementById("btn-search").addEventListener("click", () => {{
      termPrint(`search '${{document.getElementById("search-input").value.trim()}}'`, "cmd");
    }});

    document.getElementById("btn-filter").addEventListener("click", () => {{
      termPrint(`filter '${{document.getElementById("filter-input").value.trim()}}'`, "cmd");
    }});

    termPrint("simple visualizer preview ready", "info");
    termPrint("design shell matches the original UI", "muted");
    renderTree();
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
