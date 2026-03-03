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
            """
<script>
window.GVIZ_PLUGIN_BOOTSTRAP = {
  visualizerName: 'simple-visualizer',
  graph: __PAYLOAD__
};

window.GVIZ_ACTIVE_VISUALIZER = (function () {
  const palette = ['#58a6ff', '#bc8cff', '#3fb950', '#e3b341', '#79c0ff', '#f0883e', '#db61a2'];
  let selectedNodeId = null;
  let currentGraph = null;
  let simulation = null;
  let birdIntervalId = null;
  let birdTimeoutId = null;

  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  function render(graph) {
    currentGraph = graph;
    selectedNodeId = null;

    renderMainView(graph);
    renderBirdView(graph);
    renderTree(graph);
    clearDetails();
  }

  function clear() {
    currentGraph = null;
    selectedNodeId = null;

    if (simulation) {
      simulation.stop();
      simulation = null;
    }
    if (birdIntervalId) {
      clearInterval(birdIntervalId);
      birdIntervalId = null;
    }
    if (birdTimeoutId) {
      clearTimeout(birdTimeoutId);
      birdTimeoutId = null;
    }

    d3.select('#graph-canvas').selectAll('*').remove();
    const treeBody = $('#tree-body');
    if (treeBody) {
      treeBody.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:11px;text-align:center">No graph loaded</div>';
    }
    clearDetails();

    const canvas = document.getElementById('bird-view-canvas');
    if (canvas) {
      const W = canvas.clientWidth || 240;
      const H = 130;
      const ctx = canvas.getContext('2d');
      canvas.width = W;
      canvas.height = H;
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = '#0d1117';
      ctx.fillRect(0, 0, W, H);
    }
  }

  function renderMainView(graph) {
    const svg = d3.select('#graph-canvas');
    svg.selectAll('*').remove();

    const el = document.getElementById('graph-canvas');
    const W = el.clientWidth || 960;
    const H = el.clientHeight || 720;

    const defs = svg.append('defs');
    const gridPattern = defs.append('pattern')
      .attr('id', 'graph-grid')
      .attr('width', 32)
      .attr('height', 32)
      .attr('patternUnits', 'userSpaceOnUse');

    gridPattern.append('path')
      .attr('d', 'M 32 0 L 0 0 0 32')
      .attr('fill', 'none')
      .attr('stroke', '#21262d')
      .attr('stroke-width', 1);

    defs.append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -4 8 8')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-4L8,0L0,4')
      .attr('fill', '#444c56');

    svg.append('rect')
      .attr('class', 'graph-grid')
      .attr('width', W)
      .attr('height', H)
      .attr('fill', 'url(#graph-grid)');

    const g = svg.append('g').attr('class', 'graph-container');
    const zoom = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', event => g.attr('transform', event.transform));
    svg.call(zoom);

    const color = d => palette[graph.nodes.findIndex(n => n.id === d.id) % palette.length];
    const nodes = graph.nodes.map(n => ({ ...n }));
    const edges = graph.edges.map(e => ({ ...e }));

    simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id).distance(100).strength(0.5))
      .force('charge', d3.forceManyBody().strength(-320))
      .force('center', d3.forceCenter(W / 2, H / 2))
      .force('collision', d3.forceCollide(36));

    const edgeG = g.append('g').attr('class', 'edges');
    const edgeSel = edgeG.selectAll('.d3-edge')
      .data(edges)
      .enter()
      .append('g')
      .attr('class', 'd3-edge');

    edgeSel.append('line')
      .attr('class', d => graph.directed ? 'directed' : '')
      .style('stroke', '#444c56')
      .style('stroke-width', 1.5)
      .style('stroke-opacity', 0.7);

    const nodeG = g.append('g').attr('class', 'nodes');
    const nodeSel = nodeG.selectAll('.d3-node')
      .data(nodes)
      .enter()
      .append('g')
      .attr('class', 'd3-node')
      .call(
        d3.drag()
          .on('start', dragStart)
          .on('drag', dragged)
          .on('end', dragEnd)
      );

    nodeSel.append('circle')
      .attr('r', 18)
      .style('fill', d => color(d))
      .style('fill-opacity', 0.2)
      .style('stroke', d => color(d))
      .style('stroke-width', 2.5)
      .style('cursor', 'pointer');

    nodeSel.append('text')
      .text(d => ((d.attrs && d.attrs.name) || d.id).split(' ')[0])
      .attr('dy', 26)
      .style('font-size', '11px')
      .style('fill', '#8b949e')
      .style('text-anchor', 'middle')
      .style('pointer-events', 'none');

    nodeSel
      .on('mouseover', (event, d) => {
        showNodeDetails(d);
        d3.select(event.currentTarget).select('circle')
          .style('fill-opacity', d.id === selectedNodeId ? 0.2 : 0.35)
          .style('stroke-width', 3);
      })
      .on('mouseout', (event, d) => {
        d3.select(event.currentTarget).select('circle')
          .style('fill-opacity', 0.2)
          .style('stroke-width', d.id === selectedNodeId ? 5 : 2.5);
      })
      .on('click', (_, d) => {
        if (selectedNodeId === d.id) {
          clearSelection(graph);
          return;
        }
        selectNode(d.id, graph);
      });

    simulation.on('tick', () => {
      edgeSel.select('line')
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      nodeSel.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    $('#zoom-in').onclick = () => svg.transition().duration(300).call(zoom.scaleBy, 1.4);
    $('#zoom-out').onclick = () => svg.transition().duration(300).call(zoom.scaleBy, 0.7);
    $('#zoom-fit').onclick = () => {
      const bounds = g.node().getBBox();
      if (!bounds.width || !bounds.height) {
        svg.transition().duration(400).call(
          zoom.transform,
          d3.zoomIdentity.translate(W / 2, H / 2).scale(1)
        );
        return;
      }

      const padding = 48;
      const scale = Math.max(
        0.2,
        Math.min(
          2.5,
          Math.min(
            (W - padding * 2) / bounds.width,
            (H - padding * 2) / bounds.height
          )
        )
      );
      const translateX = W / 2 - scale * (bounds.x + bounds.width / 2);
      const translateY = H / 2 - scale * (bounds.y + bounds.height / 2);

      svg.transition().duration(400).call(
        zoom.transform,
        d3.zoomIdentity.translate(translateX, translateY).scale(scale)
      );
    };

    function dragStart(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnd(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  }

  function selectNode(nodeId, graph, options = {}) {
    const shouldScrollTree = options.scrollTree !== false;
    selectedNodeId = nodeId;
    if (window.GVIZ_APP_STATE) {
      window.GVIZ_APP_STATE.selectedNodeId = nodeId;
    }

    d3.selectAll('.d3-node circle')
      .classed('selected-pulse', d => d.id === nodeId)
      .style('--selected-pulse-color', d => palette[graph.nodes.findIndex(n => n.id === d.id) % palette.length])
      .style('fill-opacity', 0.2)
      .style('stroke-width', d => d.id === nodeId ? 5 : 2.5)
      .style('stroke', function (d) {
        return palette[graph.nodes.findIndex(n => n.id === d.id) % palette.length];
      });

    $$('.tree-node-row').forEach(row => {
      row.classList.toggle('selected', row.dataset.nodeId === nodeId);
      if (shouldScrollTree && row.dataset.nodeId === nodeId) {
        row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    });

    const node = graph.nodes.find(n => n.id === nodeId);
    if (node) showNodeDetails(node);

    if (typeof termPrint === 'function') {
      termPrint(`$ select --node=${nodeId}`, 'cmd');
    }
  }

  function clearSelection(graph) {
    selectedNodeId = null;
    if (window.GVIZ_APP_STATE) {
      window.GVIZ_APP_STATE.selectedNodeId = null;
    }

    d3.selectAll('.d3-node circle')
      .classed('selected-pulse', false)
      .style('fill-opacity', 0.2)
      .style('stroke-width', 2.5)
      .style('stroke', function (d) {
        return palette[graph.nodes.findIndex(n => n.id === d.id) % palette.length];
      });

    $$('.tree-node-row').forEach(row => {
      row.classList.remove('selected');
    });

    clearDetails();

    if (typeof termPrint === 'function') {
      termPrint('$ select --clear', 'cmd');
    }
  }

  function renderBirdView(graph) {
    const canvas = document.getElementById('bird-view-canvas');
    const W = canvas.clientWidth || 240;
    const H = 130;
    const ctx = canvas.getContext('2d');
    canvas.width = W;
    canvas.height = H;

    if (birdIntervalId) clearInterval(birdIntervalId);
    if (birdTimeoutId) clearTimeout(birdTimeoutId);

    birdTimeoutId = setTimeout(() => drawBirdViewSnapshot(graph, ctx, W, H), 1200);
    birdIntervalId = setInterval(() => drawBirdViewSnapshot(graph, ctx, W, H), 2500);
  }

  function drawBirdViewSnapshot(graph, ctx, W, H) {
    const nodes = d3.selectAll('.d3-node');
    if (nodes.empty()) return;

    const positions = [];
    nodes.each(d => {
      if (d.x && d.y) positions.push({ id: d.id, x: d.x, y: d.y });
    });
    if (!positions.length) return;

    const xs = positions.map(p => p.x);
    const ys = positions.map(p => p.y);
    const minX = Math.min(...xs) - 30;
    const maxX = Math.max(...xs) + 30;
    const minY = Math.min(...ys) - 30;
    const maxY = Math.max(...ys) + 30;
    const scaleX = W / (maxX - minX || 1);
    const scaleY = H / (maxY - minY || 1);
    const scale = Math.min(scaleX, scaleY) * 0.9;
    const offsetX = (W - (maxX - minX) * scale) / 2 - minX * scale;
    const offsetY = (H - (maxY - minY) * scale) / 2 - minY * scale;

    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#0d1117';
    ctx.fillRect(0, 0, W, H);

    const posMap = {};
    positions.forEach(p => {
      posMap[p.id] = { x: p.x * scale + offsetX, y: p.y * scale + offsetY };
    });

    graph.edges.forEach(e => {
      const source = posMap[e.source.id || e.source];
      const target = posMap[e.target.id || e.target];
      if (!source || !target) return;
      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      ctx.strokeStyle = '#30363d';
      ctx.lineWidth = 0.8;
      ctx.stroke();
    });

    positions.forEach((p, index) => {
      const x = posMap[p.id].x;
      const y = posMap[p.id].y;
      const color = palette[index % palette.length];
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.fillStyle = color + '55';
      ctx.fill();
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.2;
      ctx.stroke();
      if (p.id === selectedNodeId) {
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.strokeStyle = '#f0883e';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }
    });

    ctx.strokeStyle = '#58a6ff';
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    ctx.strokeRect(W * 0.15, H * 0.2, W * 0.65, H * 0.6);
    ctx.setLineDash([]);
  }

  function renderTree(graph) {
    const container = $('#tree-body');
    container.innerHTML = '';

    if (!graph.nodes.length) {
      container.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:11px;text-align:center">No graph loaded</div>';
      return;
    }

    const edgesFrom = nodeId => graph.edges.filter(e => (e.source.id || e.source) === nodeId);
    const inDegree = new Map(graph.nodes.map(node => [node.id, 0]));
    const outDegree = new Map(graph.nodes.map(node => [node.id, 0]));
    graph.edges.forEach(edge => {
      const sourceId = edge.source.id || edge.source;
      const targetId = edge.target.id || edge.target;
      outDegree.set(sourceId, (outDegree.get(sourceId) || 0) + 1);
      inDegree.set(targetId, (inDegree.get(targetId) || 0) + 1);
    });

    const rootCandidates = graph.nodes.filter(node => (inDegree.get(node.id) || 0) === 0);
    const rootPool = rootCandidates.length ? rootCandidates : graph.nodes;
    const root = rootPool.reduce((best, node) => {
      if (!best) return node;
      return (outDegree.get(node.id) || 0) > (outDegree.get(best.id) || 0) ? node : best;
    }, null) || graph.nodes[0];
    const nodeById = new Map(graph.nodes.map(node => [node.id, node]));

    function buildNodeEl(node, depth, visited) {
      if (visited.has(node.id)) {
        const row = document.createElement('div');
        row.className = 'tree-node-row';
        row.dataset.nodeId = node.id;
        row.style.paddingLeft = `${8 + depth * 16}px`;
        row.innerHTML = `
          <span class="tree-toggle leaf"></span>
          <span class="tree-icon" style="color:var(--accent-orange)">↩</span>
          <span class="tree-label" style="color:var(--text-muted);font-style:italic">${(node.attrs && node.attrs.name) || node.id} (ref)</span>
        `;
        row.addEventListener('click', () => {
          if (selectedNodeId === node.id) {
            clearSelection(graph);
            return;
          }
          selectNode(node.id, graph, { scrollTree: false });
        });
        return row;
      }

      const nextVisited = new Set(visited);
      nextVisited.add(node.id);
      const children = edgesFrom(node.id);
      const hasChildren = children.length > 0;
      const label = (node.attrs && node.attrs.name) || node.id;

      const wrap = document.createElement('div');
      wrap.className = 'tree-node';

      const row = document.createElement('div');
      row.className = 'tree-node-row';
      row.dataset.nodeId = node.id;
      row.style.paddingLeft = `${8 + depth * 16}px`;
      row.innerHTML = `
        <span class="tree-toggle ${hasChildren ? '' : 'leaf'}" data-toggle>
          ${hasChildren ? '▶' : ''}
        </span>
        <span class="tree-icon">●</span>
        <span class="tree-label">${label}</span>
        ${hasChildren ? `<span class="tree-badge">${children.length}</span>` : ''}
      `;

      const childrenDiv = document.createElement('div');
      childrenDiv.className = 'tree-children';
      let childrenBuilt = false;

      function populateChildren() {
        if (childrenBuilt) return;
        childrenBuilt = true;

        children.forEach(edge => {
          const childId = edge.target.id || edge.target;
          const childNode = nodeById.get(childId);
          if (childNode) {
            childrenDiv.appendChild(buildNodeEl(childNode, depth + 1, nextVisited));
          }
        });
      }

      if (hasChildren) {
        const toggle = row.querySelector('[data-toggle]');
        row.addEventListener('click', () => {
          if (selectedNodeId === node.id) {
            clearSelection(graph);
          } else {
            selectNode(node.id, graph, { scrollTree: false });
          }
          const open = childrenDiv.classList.toggle('open');
          if (open) {
            populateChildren();
          }
          toggle.textContent = open ? '▼' : '▶';
          toggle.classList.toggle('expanded', open);
        });
      } else {
        row.addEventListener('click', () => {
          if (selectedNodeId === node.id) {
            clearSelection(graph);
            return;
          }
          selectNode(node.id, graph, { scrollTree: false });
        });
      }

      wrap.appendChild(row);
      wrap.appendChild(childrenDiv);
      return wrap;
    }

    container.appendChild(buildNodeEl(root, 0, new Set()));
  }

  function showNodeDetails(node) {
    const body = $('#node-details-body');
    const attrs = node.attrs || {};

    const typeClass = value => {
      if (value instanceof Date || (typeof value === 'string' && /^\\d{4}-\\d{2}-\\d{2}$/.test(value))) return 'type-date';
      if (Number.isInteger(value)) return 'type-int';
      if (typeof value === 'number') return 'type-float';
      return 'type-str';
    };

    let html = `
      <div class="detail-node-id">
        <span class="node-color-dot"></span>
        <span class="node-id-text">${node.id}</span>
      </div>
      <div class="detail-divider"></div>
    `;

    for (const [key, value] of Object.entries(attrs)) {
      html += `
        <div class="detail-row">
          <span class="detail-key">${key}</span>
          <span class="detail-val ${typeClass(value)}">${value}</span>
        </div>
      `;
    }

    body.innerHTML = html;
  }

  function clearDetails() {
    const body = $('#node-details-body');
    if (!body) return;
    body.innerHTML = `
      <div class="detail-empty">
        <svg width="24" height="24" viewBox="0 0 16 16" fill="var(--text-muted)">
          <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
          <path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
        </svg>
        Hover or click a node
      </div>
    `;
  }

  return {
    render,
    clear
  };
})();
</script>
""".replace("__PAYLOAD__", payload_json)
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
