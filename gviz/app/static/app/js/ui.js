/* ============================================================
   gviz — UI interactions (mock/static version)
   All backend calls are stubbed with TODO comments.
   ============================================================ */

'use strict';

/* ── Mock graph data (will come from backend later) ───────── */
const MOCK_GRAPH = {
  directed: true,
  nodes: [
    { id: 'user-001', attrs: { name: 'Alice Smith',    age: 28, score: 9.5,  city: 'New York',  join_date: '2020-03-15', company: 'TechCorp'  } },
    { id: 'user-002', attrs: { name: 'Bob Johnson',    age: 34, score: 7.2,  city: 'London',    join_date: '2019-07-22', company: 'DataSoft'  } },
    { id: 'user-003', attrs: { name: 'Carol Williams', age: 25, score: 8.8,  city: 'Berlin',    join_date: '2021-01-10', company: 'TechCorp'  } },
    { id: 'user-004', attrs: { name: 'David Brown',    age: 41, score: 6.1,  city: 'Paris',     join_date: '2018-11-05', company: 'NetWorks'  } },
    { id: 'user-005', attrs: { name: 'Eva Garcia',     age: 30, score: 8.3,  city: 'Madrid',    join_date: '2020-09-18', company: 'DataSoft'  } },
    { id: 'user-006', attrs: { name: 'Frank Miller',   age: 37, score: 5.9,  city: 'Sydney',    join_date: '2017-04-30', company: 'CloudBase' } },
    { id: 'user-007', attrs: { name: 'Grace Davis',    age: 22, score: 9.1,  city: 'Tokyo',     join_date: '2022-06-08', company: 'AlgoLab'   } },
    { id: 'user-008', attrs: { name: 'Henry Wilson',   age: 55, score: 7.7,  city: 'Toronto',   join_date: '2015-02-14', company: 'ByteWave'  } },
    { id: 'user-009', attrs: { name: 'Iris Lopez',     age: 29, score: 8.0,  city: 'Singapore', join_date: '2021-08-01', company: 'TechCorp'  } },
    { id: 'user-010', attrs: { name: 'Jack Martinez',  age: 33, score: 6.8,  city: 'Dubai',     join_date: '2019-03-27', company: 'PixelStudio'} },
  ],
  edges: [
    { id: 'e1',  source: 'user-001', target: 'user-002' },
    { id: 'e2',  source: 'user-001', target: 'user-003' },
    { id: 'e3',  source: 'user-002', target: 'user-004' },
    { id: 'e4',  source: 'user-002', target: 'user-005' },
    { id: 'e5',  source: 'user-003', target: 'user-006' },
    { id: 'e6',  source: 'user-003', target: 'user-007' },
    { id: 'e7',  source: 'user-004', target: 'user-008' },
    { id: 'e8',  source: 'user-001', target: 'user-009' },
    { id: 'e9',  source: 'user-009', target: 'user-010' },
    { id: 'e10', source: 'user-005', target: 'user-001' },  // back-edge (cycle)
    { id: 'e11', source: 'user-007', target: 'user-009' },
    { id: 'e12', source: 'user-010', target: 'user-002' },
  ],
};

/* ── State ───────────────────────────────────────────────── */
const state = {
  selectedNodeId: null,
  graph: null,
  simulation: null,
};

/* ── DOM refs ─────────────────────────────────────────────── */
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

/* ═══════════════════════════════════════════════════════════
   INIT
   ═══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  setupWorkspaceTabs();
  setupModal();
  setupTreeToggle();
  setupTerminal();
  setupVizToggle();
  renderMockGraph(MOCK_GRAPH);
  renderBirdView(MOCK_GRAPH);
  renderTree(MOCK_GRAPH);
  setupSearchFilter();
});

/* ═══════════════════════════════════════════════════════════
   WORKSPACE TABS
   ═══════════════════════════════════════════════════════════ */
function setupWorkspaceTabs() {
  let wsCounter = 2;

  $$('.ws-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      if (e.target.closest('.ws-close')) return;
      $$('.ws-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
    });
    const closeBtn = tab.querySelector('.ws-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if ($$('.ws-tab').length > 1) {
          tab.remove();
          const remaining = $$('.ws-tab');
          if (remaining.length && !$('.ws-tab.active')) {
            remaining[remaining.length - 1].classList.add('active');
          }
        }
      });
    }
  });

  $('.ws-tab-add').addEventListener('click', () => {
    wsCounter++;
    const tab = document.createElement('div');
    tab.className = 'ws-tab active';
    tab.innerHTML = `
      <span class="ws-dot" style="background:#bc8cff"></span>
      Workspace ${wsCounter}
      <span class="ws-close">✕</span>
    `;
    $$('.ws-tab').forEach(t => t.classList.remove('active'));
    $('.ws-tab-add').before(tab);

    // Re-attach listeners
    tab.addEventListener('click', (e) => {
      if (e.target.closest('.ws-close')) return;
      $$('.ws-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
    });
    tab.querySelector('.ws-close').addEventListener('click', (e) => {
      e.stopPropagation();
      if ($$('.ws-tab').length > 1) {
        tab.remove();
        const remaining = $$('.ws-tab');
        if (remaining.length && !$('.ws-tab.active')) {
          remaining[remaining.length - 1].classList.add('active');
        }
      }
    });
    showToast(`Workspace ${wsCounter} created`, 'info');
    termPrint(`info Workspace ${wsCounter} opened`, 'info');
  });
}

/* ═══════════════════════════════════════════════════════════
   MODAL (Load Data)
   ═══════════════════════════════════════════════════════════ */
function setupModal() {
  const backdrop = $('#load-modal');
  const openBtn  = $('#btn-load-data');
  const closeBtn = $('#modal-close');
  const cancelBtn = $('#modal-cancel');
  const confirmBtn = $('#modal-confirm');
  const pluginSel = $('#modal-plugin-select');

  openBtn.addEventListener('click', () => backdrop.classList.add('open'));
  closeBtn.addEventListener('click', () => backdrop.classList.remove('open'));
  cancelBtn.addEventListener('click', () => backdrop.classList.remove('open'));
  backdrop.addEventListener('click', (e) => { if (e.target === backdrop) backdrop.classList.remove('open'); });

  pluginSel.addEventListener('change', () => {
    // TODO: fetch plugin parameters from backend GET /api/plugin-params/?name=...
    // and dynamically render form fields
    const name = pluginSel.value;
    updateModalParams(name);
  });

  confirmBtn.addEventListener('click', () => {
    const plugin = pluginSel.value;
    const filePath = $('#param-file-path').value.trim();
    if (!filePath) { showToast('File path is required', 'error'); return; }

    // TODO: POST /api/load-graph/ { plugin, file_path: filePath, directed: true }
    backdrop.classList.remove('open');
    termPrint(`$ load --plugin=${plugin} --file="${filePath}"`, 'cmd');
    termPrint(`  Loading graph from "${filePath}" using [${plugin}]...`, 'info');
    // Simulate success
    setTimeout(() => {
      termPrint(`  ✓ Graph loaded: ${MOCK_GRAPH.nodes.length} nodes, ${MOCK_GRAPH.edges.length} edges`, 'info');
      showToast(`Graph loaded (${MOCK_GRAPH.nodes.length} nodes, ${MOCK_GRAPH.edges.length} edges)`, 'success');
    }, 600);
  });
}

function updateModalParams(pluginName) {
  // TODO: replace with actual backend-driven params
  const wrap = $('#modal-params');
  if (pluginName === 'json-data-source') {
    wrap.innerHTML = `
      <div class="form-group">
        <label class="form-label">File Path</label>
        <input id="param-file-path" type="text" class="form-input"
          placeholder="e.g. data/social_network.json">
        <span class="form-hint">Absolute or relative path to the <code>.json</code> file</span>
      </div>
      <div class="form-group">
        <label class="form-label">Graph Type</label>
        <select id="param-directed" class="form-input">
          <option value="true">Directed</option>
          <option value="false">Undirected</option>
        </select>
      </div>
    `;
  } else if (pluginName === 'xml-data-source') {
    wrap.innerHTML = `
      <div class="form-group">
        <label class="form-label">File Path</label>
        <input id="param-file-path" type="text" class="form-input"
          placeholder="e.g. data/network.xml">
        <span class="form-hint">Absolute or relative path to the <code>.xml</code> file</span>
      </div>
    `;
  }
}

/* ═══════════════════════════════════════════════════════════
   VISUALIZER TOGGLE (Simple / Block)
   ═══════════════════════════════════════════════════════════ */
function setupVizToggle() {
  $$('.viz-toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.viz-toggle-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const mode = btn.dataset.mode;
      termPrint(`$ visualizer --mode=${mode}`, 'cmd');
      // TODO: POST /api/set-visualizer/ { name: mode }  → re-render graph
      showToast(`Visualizer: ${mode}`, 'info');
    });
  });
}

/* ═══════════════════════════════════════════════════════════
   MAIN VIEW — D3 force-directed graph
   ═══════════════════════════════════════════════════════════ */
function renderMockGraph(graph) {
  const svg = d3.select('#graph-canvas');
  svg.selectAll('*').remove();
  const el = document.getElementById('graph-canvas');
  const W = el.clientWidth, H = el.clientHeight;

  /* Arrowhead marker */
  const defs = svg.append('defs');
  defs.append('marker')
    .attr('id', 'arrowhead')
    .attr('viewBox', '0 -4 8 8')
    .attr('refX', 20).attr('refY', 0)
    .attr('markerWidth', 6).attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path').attr('d', 'M0,-4L8,0L0,4').attr('fill', '#444c56');

  const g = svg.append('g').attr('class', 'graph-container');

  /* Zoom behaviour */
  const zoom = d3.zoom()
    .scaleExtent([0.2, 4])
    .on('zoom', e => g.attr('transform', e.transform));
  svg.call(zoom);

  /* ─ Colour scale ─ */
  const palette = ['#58a6ff','#bc8cff','#3fb950','#e3b341','#79c0ff','#f0883e','#db61a2'];
  const color = d => palette[graph.nodes.findIndex(n => n.id === d.id) % palette.length];

  /* ─ Build D3 data ─ */
  const nodes = graph.nodes.map(n => ({ ...n }));
  const edges = graph.edges.map(e => ({ ...e }));

  /* ─ Force simulation ─ */
  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(edges).id(d => d.id).distance(100).strength(0.5))
    .force('charge', d3.forceManyBody().strength(-320))
    .force('center', d3.forceCenter(W / 2, H / 2))
    .force('collision', d3.forceCollide(36));
  state.simulation = simulation;

  /* ─ Edges ─ */
  const edgeG = g.append('g').attr('class', 'edges');
  const edgeSel = edgeG.selectAll('.d3-edge')
    .data(edges).enter().append('g').attr('class', 'd3-edge');
  edgeSel.append('line')
    .attr('class', d => graph.directed ? 'directed' : '')
    .style('stroke', '#444c56')
    .style('stroke-width', 1.5)
    .style('stroke-opacity', 0.7);

  /* ─ Nodes ─ */
  const nodeG = g.append('g').attr('class', 'nodes');
  const nodeSel = nodeG.selectAll('.d3-node')
    .data(nodes).enter().append('g').attr('class', 'd3-node')
    .call(d3.drag()
      .on('start', dragStart)
      .on('drag',  dragged)
      .on('end',   dragEnd));

  nodeSel.append('circle')
    .attr('r', 18)
    .style('fill', d => color(d))
    .style('fill-opacity', 0.2)
    .style('stroke', d => color(d))
    .style('stroke-width', 2.5)
    .style('cursor', 'pointer');

  nodeSel.append('text')
    .text(d => (d.attrs.name || d.id).split(' ')[0])
    .attr('dy', 26)
    .style('font-size', '11px')
    .style('fill', '#8b949e')
    .style('text-anchor', 'middle')
    .style('pointer-events', 'none');

  /* Mouseover / click */
  nodeSel
    .on('mouseover', (e, d) => {
      showNodeDetails(d);
      d3.select(e.currentTarget).select('circle')
        .style('fill-opacity', 0.35).style('stroke-width', 3);
    })
    .on('mouseout', (e, d) => {
      if (state.selectedNodeId !== d.id) {
        d3.select(e.currentTarget).select('circle')
          .style('fill-opacity', 0.2).style('stroke-width', 2.5);
      }
    })
    .on('click', (e, d) => selectNode(d.id, graph));

  /* Simulation tick */
  simulation.on('tick', () => {
    edgeSel.select('line')
      .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x).attr('y2', d => d.target.y);
    nodeSel.attr('transform', d => `translate(${d.x},${d.y})`);
  });

  /* Zoom buttons */
  $('#zoom-in').onclick  = () => svg.transition().duration(300).call(zoom.scaleBy, 1.4);
  $('#zoom-out').onclick = () => svg.transition().duration(300).call(zoom.scaleBy, 0.7);
  $('#zoom-fit').onclick = () => svg.transition().duration(400).call(zoom.transform, d3.zoomIdentity.translate(W/2,H/2).scale(0.9));

  /* Drag helpers */
  function dragStart(e, d) {
    if (!e.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x; d.fy = d.y;
  }
  function dragged(e, d) { d.fx = e.x; d.fy = e.y; }
  function dragEnd(e, d) {
    if (!e.active) simulation.alphaTarget(0);
    d.fx = null; d.fy = null;
  }
}

/* ── Node selection (coordinated across all 3 views) ──────── */
function selectNode(nodeId, graph) {
  state.selectedNodeId = nodeId;

  /* Highlight in Main View */
  d3.selectAll('.d3-node circle')
    .style('fill-opacity', d => d.id === nodeId ? 0.45 : 0.2)
    .style('stroke-width', d => d.id === nodeId ? 3.5 : 2.5)
    .style('stroke', function(d) {
      if (d.id === nodeId) return 'var(--node-selected)';
      const palette = ['#58a6ff','#bc8cff','#3fb950','#e3b341','#79c0ff','#f0883e','#db61a2'];
      return palette[graph.nodes.findIndex(n => n.id === d.id) % palette.length];
    });

  /* Highlight in Tree View */
  $$('.tree-node-row').forEach(row => {
    row.classList.toggle('selected', row.dataset.nodeId === nodeId);
    if (row.dataset.nodeId === nodeId) {
      row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  });

  /* Show details */
  const node = graph.nodes.find(n => n.id === nodeId);
  if (node) showNodeDetails(node);

  termPrint(`$ select --node=${nodeId}`, 'cmd');
}

/* ═══════════════════════════════════════════════════════════
   BIRD VIEW
   ═══════════════════════════════════════════════════════════ */
function renderBirdView(graph) {
  const canvas = document.getElementById('bird-view-canvas');
  const W = canvas.clientWidth || 240;
  const H = 130;
  const ctx = canvas.getContext('2d');
  canvas.width = W; canvas.height = H;

  // Wait for D3 simulation to settle, then draw snapshot
  setTimeout(() => drawBirdViewSnapshot(graph, ctx, W, H), 2000);
  setInterval(() => drawBirdViewSnapshot(graph, ctx, W, H), 3000);
}

function drawBirdViewSnapshot(graph, ctx, W, H) {
  const nodes = d3.selectAll('.d3-node');
  if (nodes.empty()) return;

  const positions = [];
  nodes.each(d => { if (d.x && d.y) positions.push({ id: d.id, x: d.x, y: d.y }); });
  if (!positions.length) return;

  const xs = positions.map(p => p.x), ys = positions.map(p => p.y);
  const minX = Math.min(...xs) - 30, maxX = Math.max(...xs) + 30;
  const minY = Math.min(...ys) - 30, maxY = Math.max(...ys) + 30;
  const scaleX = W / (maxX - minX || 1);
  const scaleY = H / (maxY - minY || 1);
  const scale  = Math.min(scaleX, scaleY) * 0.9;
  const offsetX = (W - (maxX - minX) * scale) / 2 - minX * scale;
  const offsetY = (H - (maxY - minY) * scale) / 2 - minY * scale;

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = '#0d1117';
  ctx.fillRect(0, 0, W, H);

  const palette = ['#58a6ff','#bc8cff','#3fb950','#e3b341','#79c0ff','#f0883e','#db61a2'];
  const posMap = {};
  positions.forEach(p => posMap[p.id] = { x: p.x * scale + offsetX, y: p.y * scale + offsetY });

  // Draw edges
  graph.edges.forEach(e => {
    const s = posMap[e.source.id || e.source];
    const t = posMap[e.target.id || e.target];
    if (!s || !t) return;
    ctx.beginPath();
    ctx.moveTo(s.x, s.y); ctx.lineTo(t.x, t.y);
    ctx.strokeStyle = '#30363d'; ctx.lineWidth = 0.8;
    ctx.stroke();
  });

  // Draw nodes
  positions.forEach((p, i) => {
    const x = posMap[p.id].x, y = posMap[p.id].y;
    const c = palette[i % palette.length];
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fillStyle = c + '55';
    ctx.fill();
    ctx.strokeStyle = c;
    ctx.lineWidth = 1.2;
    ctx.stroke();
    if (p.id === state.selectedNodeId) {
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, Math.PI * 2);
      ctx.strokeStyle = '#f0883e';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  });

  // Viewport rectangle (static placeholder, will sync with pan/zoom)
  ctx.strokeStyle = '#58a6ff';
  ctx.lineWidth = 1;
  ctx.setLineDash([3, 3]);
  ctx.strokeRect(W * 0.15, H * 0.2, W * 0.65, H * 0.6);
  ctx.setLineDash([]);
}

/* ═══════════════════════════════════════════════════════════
   TREE VIEW
   ═══════════════════════════════════════════════════════════ */
function renderTree(graph) {
  const container = $('#tree-body');
  container.innerHTML = '';

  if (!graph.nodes.length) {
    container.innerHTML = '<div style="padding:12px;color:var(--text-muted);font-size:11px;text-align:center">No graph loaded</div>';
    return;
  }

  // Pick root = first node
  const root = graph.nodes[0];
  const edgesFrom = (nodeId) => graph.edges.filter(e => (e.source.id || e.source) === nodeId);

  function buildNodeEl(node, depth, visited) {
    if (visited.has(node.id)) {
      // Cycle detected — show stub with link icon
      const row = document.createElement('div');
      row.className = 'tree-node-row';
      row.dataset.nodeId = node.id;
      row.style.paddingLeft = `${8 + depth * 16}px`;
      row.innerHTML = `
        <span class="tree-toggle leaf"></span>
        <span class="tree-icon" style="color:var(--accent-orange)">↩</span>
        <span class="tree-label" style="color:var(--text-muted);font-style:italic">${node.attrs.name || node.id} (ref)</span>
      `;
      row.addEventListener('click', () => selectNode(node.id, graph));
      return row;
    }

    const newVisited = new Set(visited);
    newVisited.add(node.id);
    const children = edgesFrom(node.id);
    const hasChildren = children.length > 0;
    const label = node.attrs.name || node.id;

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

    if (hasChildren) {
      const toggle = row.querySelector('[data-toggle]');
      row.addEventListener('click', (e) => {
        if (e.target.closest('[data-toggle]') || e.currentTarget === e.target) {
          // expand/collapse
        }
        selectNode(node.id, graph);
        const open = childrenDiv.classList.toggle('open');
        toggle.textContent = open ? '▼' : '▶';
        toggle.classList.toggle('expanded', open);
      });

      children.forEach(edge => {
        const childId = edge.target.id || edge.target;
        const childNode = graph.nodes.find(n => n.id === childId);
        if (childNode) {
          childrenDiv.appendChild(buildNodeEl(childNode, depth + 1, newVisited));
        }
      });
    } else {
      row.addEventListener('click', () => selectNode(node.id, graph));
    }

    wrap.appendChild(row);
    wrap.appendChild(childrenDiv);
    return wrap;
  }

  container.appendChild(buildNodeEl(root, 0, new Set()));
}

/* ═══════════════════════════════════════════════════════════
   NODE DETAILS PANEL
   ═══════════════════════════════════════════════════════════ */
function showNodeDetails(node) {
  const body = $('#node-details-body');
  const attrs = node.attrs || node.get_attributes?.() || {};

  const typeClass = (val) => {
    if (val instanceof Date || (typeof val === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(val))) return 'type-date';
    if (Number.isInteger(val)) return 'type-int';
    if (typeof val === 'number') return 'type-float';
    return 'type-str';
  };

  let html = `
    <div class="detail-node-id">
      <span class="node-color-dot"></span>
      <span class="node-id-text">${node.id}</span>
    </div>
    <div class="detail-divider"></div>
  `;

  for (const [key, val] of Object.entries(attrs)) {
    html += `
      <div class="detail-row">
        <span class="detail-key">${key}</span>
        <span class="detail-val ${typeClass(val)}">${val}</span>
      </div>
    `;
  }

  body.innerHTML = html;
}

/* ═══════════════════════════════════════════════════════════
   TREE VIEW TOGGLE (panel collapse)
   ═══════════════════════════════════════════════════════════ */
function setupTreeToggle() {
  // Panel collapse buttons
  $$('.panel-collapse-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.panel;
      const panel = document.getElementById(target);
      if (!panel) return;
      panel.style.display = panel.style.display === 'none' ? '' : 'none';
    });
  });
}

/* ═══════════════════════════════════════════════════════════
   SEARCH & FILTER
   ═══════════════════════════════════════════════════════════ */
function setupSearchFilter() {
  const searchInput = $('#search-input');
  const filterInput = $('#filter-input');
  const searchBtn   = $('#btn-search');
  const filterBtn   = $('#btn-filter');
  const resetBtn    = $('#btn-reset');

  searchBtn.addEventListener('click', () => doSearch(searchInput.value.trim()));
  searchInput.addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(searchInput.value.trim()); });

  filterBtn.addEventListener('click', () => doFilter(filterInput.value.trim()));
  filterInput.addEventListener('keydown', e => { if (e.key === 'Enter') doFilter(filterInput.value.trim()); });

  resetBtn.addEventListener('click', () => {
    searchInput.value = '';
    filterInput.value = '';
    // TODO: POST /api/workspace/reset/
    termPrint('$ reset', 'cmd');
    termPrint('  ✓ Workspace reset to original graph', 'info');
    showToast('Graph reset', 'info');
    renderMockGraph(MOCK_GRAPH);
    renderTree(MOCK_GRAPH);
  });
}

function doSearch(query) {
  if (!query) return;
  termPrint(`$ search '${query}'`, 'cmd');
  // TODO: POST /api/search/ { query }  → returns subgraph JSON
  // For now: client-side mock (spec says server-side, TODO to replace)
  const matching = MOCK_GRAPH.nodes.filter(n =>
    Object.entries(n.attrs).some(([k, v]) =>
      k.toLowerCase().includes(query.toLowerCase()) ||
      String(v).toLowerCase().includes(query.toLowerCase())
    )
  );
  termPrint(`  ✓ ${matching.length} node(s) match "${query}"`, 'info');
  showToast(`Search: ${matching.length} nodes found`, 'success');
}

function doFilter(expr) {
  if (!expr) return;
  termPrint(`$ filter '${expr}'`, 'cmd');
  // TODO: POST /api/filter/ { expression: expr }  → returns subgraph JSON
  showToast(`Filter applied: ${expr}`, 'success');
}

/* ═══════════════════════════════════════════════════════════
   TERMINAL
   ═══════════════════════════════════════════════════════════ */
function setupTerminal() {
  const input   = $('#term-input');
  const output  = $('#term-output');
  const history = [];
  let histIdx   = -1;

  // Welcome message
  termPrint('gviz v1.0.0 — Graph Visualizer', 'info');
  termPrint('Type `help` for available commands.', 'muted');

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      const cmd = input.value.trim();
      if (!cmd) return;
      history.unshift(cmd);
      histIdx = -1;
      input.value = '';
      handleTermCommand(cmd);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      histIdx = Math.min(histIdx + 1, history.length - 1);
      input.value = history[histIdx] || '';
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      histIdx = Math.max(histIdx - 1, -1);
      input.value = histIdx === -1 ? '' : history[histIdx];
    }
  });

  // Focus terminal on click
  document.querySelector('.terminal-panel').addEventListener('click', () => input.focus());
}

function handleTermCommand(cmd) {
  termPrint(`gviz > ${cmd}`, 'cmd');
  const parts = cmd.trim().split(/\s+/);
  const verb  = parts[0].toLowerCase();

  if (verb === 'help') {
    termPrint('  Commands:', 'muted');
    termPrint('    create node --id=<id> --property <key>=<val> ...', 'muted');
    termPrint('    create edge --id=<id> <source_id> <target_id>', 'muted');
    termPrint('    edit   node --id=<id> --property <key>=<val>', 'muted');
    termPrint('    delete node --id=<id>', 'muted');
    termPrint('    delete edge --id=<id>', 'muted');
    termPrint('    search <query>', 'muted');
    termPrint('    filter <attr> <op> <value>', 'muted');
    termPrint('    reset', 'muted');
    termPrint('    clear', 'muted');
  } else if (verb === 'clear') {
    $('#term-output').innerHTML = '';
  } else if (verb === 'search') {
    const q = parts.slice(1).join(' ').replace(/['"]/g, '');
    doSearch(q);
  } else if (verb === 'filter') {
    const expr = parts.slice(1).join(' ').replace(/['"]/g, '');
    doFilter(expr);
  } else if (verb === 'reset') {
    termPrint('  ✓ Graph reset', 'info');
    showToast('Graph reset', 'info');
  } else if (verb === 'create' || verb === 'edit' || verb === 'delete') {
    // TODO: POST /api/cli/ { command: cmd }
    termPrint(`  → Command received. (TODO: connect to backend)`, 'info');
  } else {
    termPrint(`  ✗ Unknown command: '${verb}'. Type 'help'.`, 'error');
  }
}

function termPrint(text, cls = '') {
  const output = $('#term-output');
  const line = document.createElement('div');
  line.className = `term-line ${cls}`;
  line.textContent = text;
  output.appendChild(line);
  output.scrollTop = output.scrollHeight;
}

/* ═══════════════════════════════════════════════════════════
   TOAST NOTIFICATIONS
   ═══════════════════════════════════════════════════════════ */
function showToast(msg, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = msg;
  document.body.appendChild(toast);
  requestAnimationFrame(() => {
    requestAnimationFrame(() => toast.classList.add('show'));
  });
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}
