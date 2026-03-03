/* ============================================================
   gviz — UI shell
   Student 2 visualizer logic is provided by the selected plugin.
   ============================================================ */

'use strict';

const state = {
  selectedNodeId: null,
  graph: null,
  originalGraph: null,
};

window.GVIZ_APP_STATE = state;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

document.addEventListener('DOMContentLoaded', () => {
  setupWorkspaceTabs();
  setupPluginSelection();
  setupTreeToggle();
  setupTerminal();
  setupVizToggle();
  setupSearchFilter();
  bootGraph();
});

function setupWorkspaceTabs() {
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
      });
    }
  });
}

function setupPluginSelection() {
  const pluginSelect = $('#plugin-select');
  const loadButton = $('#btn-load-data');

  if (loadButton && pluginSelect) {
    loadButton.addEventListener('click', () => pluginSelect.focus());
  }

  if (!pluginSelect) return;

  pluginSelect.addEventListener('change', () => {
    const plugin = pluginSelect.value;
    if (!plugin) {
      window.location.href = '/';
      return;
    }
    window.location.href = `/?plugin=${encodeURIComponent(plugin)}`;
  });
}

function bootGraph() {
  if (window.GVIZ_LOAD_ERROR) {
    showEmptyGraph();
    termPrint(`error ${window.GVIZ_LOAD_ERROR}`, 'error');
    showToast(window.GVIZ_LOAD_ERROR, 'error');
    return;
  }

  const bootstrap = window.GVIZ_PLUGIN_BOOTSTRAP;
  if (!bootstrap || !bootstrap.graph) {
    showEmptyGraph();
    termPrint('info No graph loaded. Select a plugin to start.', 'info');
    return;
  }

  state.originalGraph = cloneGraph(bootstrap.graph);
  setGraph(cloneGraph(bootstrap.graph));
  termPrint(`info Loaded ${bootstrap.visualizerName}`, 'info');
}

function cloneGraph(graph) {
  return JSON.parse(JSON.stringify(graph));
}

function setGraph(graph) {
  state.graph = graph;
  state.selectedNodeId = null;
  document.body.classList.remove('app-empty-state');
  updateGraphStats(graph);
  $('#canvas-overlay').classList.add('hidden');

  if (window.GVIZ_ACTIVE_VISUALIZER && typeof window.GVIZ_ACTIVE_VISUALIZER.render === 'function') {
    window.GVIZ_ACTIVE_VISUALIZER.render(graph);
    return;
  }

  showEmptyGraph();
  termPrint('error No active visualizer runtime found.', 'error');
}

function showEmptyGraph() {
  state.graph = null;
  state.selectedNodeId = null;
  document.body.classList.add('app-empty-state');
  updateGraphStats(null);

  if (window.GVIZ_ACTIVE_VISUALIZER && typeof window.GVIZ_ACTIVE_VISUALIZER.clear === 'function') {
    window.GVIZ_ACTIVE_VISUALIZER.clear();
  }

  $('#canvas-overlay').classList.remove('hidden');
}

function updateGraphStats(graph) {
  $('#stat-node-count').textContent = graph ? graph.nodes.length : '0';
  $('#stat-edge-count').textContent = graph ? graph.edges.length : '0';
  $('#stat-graph-kind').textContent = graph
    ? (graph.directed ? 'directed' : 'undirected')
    : 'no graph';
}

function setupTreeToggle() {
  $$('.panel-collapse-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.panel;
      const panel = document.getElementById(target);
      if (!panel) return;
      panel.style.display = panel.style.display === 'none' ? '' : 'none';
    });
  });
}

function setupVizToggle() {
  $$('.viz-toggle-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      $$('.viz-toggle-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      termPrint(`$ visualizer --mode=${btn.dataset.mode}`, 'cmd');
    });
  });
}

function setupSearchFilter() {
  const searchInput = $('#search-input');
  const filterInput = $('#filter-input');
  const searchBtn = $('#btn-search');
  const filterBtn = $('#btn-filter');
  const resetBtn = $('#btn-reset');

  searchBtn.addEventListener('click', () => doSearch(searchInput.value.trim()));
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doSearch(searchInput.value.trim());
  });

  filterBtn.addEventListener('click', () => doFilter(filterInput.value.trim()));
  filterInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doFilter(filterInput.value.trim());
  });

  resetBtn.addEventListener('click', () => {
    searchInput.value = '';
    filterInput.value = '';
    if (!state.originalGraph) {
      showToast('No graph loaded', 'error');
      return;
    }
    termPrint('$ reset', 'cmd');
    termPrint('  ✓ Workspace reset to original graph', 'info');
    showToast('Graph reset', 'info');
    setGraph(cloneGraph(state.originalGraph));
  });
}

function doSearch(query) {
  if (!query) return;
  if (!state.graph) {
    showToast('No graph loaded', 'error');
    return;
  }

  termPrint(`$ search '${query}'`, 'cmd');

  const matchingIds = state.graph.nodes
    .filter(node =>
      Object.entries(node.attrs || {}).some(([key, value]) =>
        key.toLowerCase().includes(query.toLowerCase()) ||
        String(value).toLowerCase().includes(query.toLowerCase())
      )
    )
    .map(node => node.id);

  const idSet = new Set(matchingIds);
  const nextGraph = {
    directed: state.originalGraph.directed,
    nodes: state.originalGraph.nodes.filter(node => idSet.has(node.id)),
    edges: state.originalGraph.edges.filter(edge => idSet.has(edge.source) && idSet.has(edge.target)),
  };

  termPrint(`  ✓ ${nextGraph.nodes.length} node(s) match "${query}"`, 'info');
  showToast(`Search: ${nextGraph.nodes.length} nodes found`, 'success');
  setGraph(nextGraph);
}

function doFilter(expr) {
  if (!expr) return;
  if (!state.graph) {
    showToast('No graph loaded', 'error');
    return;
  }

  termPrint(`$ filter '${expr}'`, 'cmd');
  showToast(`Filter not wired yet: ${expr}`, 'info');
}

function setupTerminal() {
  const input = $('#term-input');
  const history = [];
  let histIdx = -1;

  termPrint('gviz v1.0.0 — Graph Visualizer', 'info');
  termPrint('Select a plugin to render a graph.', 'muted');

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

  document.querySelector('.terminal-panel').addEventListener('click', () => input.focus());
}

function handleTermCommand(cmd) {
  termPrint(`gviz > ${cmd}`, 'cmd');
  const parts = cmd.trim().split(/\s+/);
  const verb = parts[0].toLowerCase();

  if (verb === 'help') {
    termPrint('  Commands:', 'muted');
    termPrint('    search <query>', 'muted');
    termPrint('    filter <attr> <op> <value>', 'muted');
    termPrint('    reset', 'muted');
    termPrint('    clear', 'muted');
    return;
  }

  if (verb === 'clear') {
    $('#term-output').innerHTML = '';
    return;
  }

  if (verb === 'search') {
    doSearch(parts.slice(1).join(' ').replace(/['"]/g, ''));
    return;
  }

  if (verb === 'filter') {
    doFilter(parts.slice(1).join(' ').replace(/['"]/g, ''));
    return;
  }

  if (verb === 'reset') {
    if (state.originalGraph) {
      setGraph(cloneGraph(state.originalGraph));
      termPrint('  ✓ Graph reset', 'info');
    } else {
      termPrint('  ✗ No graph loaded', 'error');
    }
    return;
  }

  termPrint(`  ✗ Unknown command: '${verb}'. Type 'help'.`, 'error');
}

function termPrint(text, cls = '') {
  const output = $('#term-output');
  const line = document.createElement('div');
  line.className = `term-line ${cls}`;
  line.textContent = text;
  output.appendChild(line);
  output.scrollTop = output.scrollHeight;
}

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
