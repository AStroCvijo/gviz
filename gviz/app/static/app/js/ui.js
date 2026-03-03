/* ============================================================
   gviz — UI shell
   Student 2 visualizer logic is provided by the selected plugin.
   ============================================================ */

'use strict';

const state = {
  selectedNodeId: null,
  graph: null,
  originalGraph: null,
  activePlugin: '',
};

window.GVIZ_APP_STATE = state;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

document.addEventListener('DOMContentLoaded', () => {
  setupWorkspaceTabs();
  setupPluginSelection();
  setupLoadDataModal();
  setupPredefinedLoader();
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

  if (!pluginSelect || !loadButton) return;

  pluginSelect.addEventListener('change', () => {
    const plugin = pluginSelect.value;
    if (!plugin) {
      unloadPlugin();
      return;
    }

    state.activePlugin = plugin;
    const workspaceName = $('#workspace-name');
    if (workspaceName) {
      workspaceName.textContent = 'No Workspace';
    }
    if (window.GVIZ_ACTIVE_VISUALIZER && typeof window.GVIZ_ACTIVE_VISUALIZER.clear === 'function') {
      window.GVIZ_ACTIVE_VISUALIZER.clear();
    }
    window.GVIZ_PLUGIN_BOOTSTRAP = null;
    window.GVIZ_ACTIVE_VISUALIZER = null;
    state.originalGraph = null;
    showEmptyGraph();
    termPrint(`info Selected ${plugin}. Click Load Data to continue.`, 'info');
    showToast('Plugin selected', 'info');
  });
}

function setupLoadDataModal() {
  const loadButton = $('#btn-load-data');
  const pluginSelect = $('#plugin-select');
  const modal = $('#load-data-modal');
  const closeBtn = $('#load-data-close');
  const cancelBtn = $('#load-data-cancel');
  const confirmBtn = $('#load-data-confirm');
  const sourceSelect = $('#data-source-select');
  const filePresetSelect = $('#data-file-preset');
  const fileInput = $('#data-file-path');
  const directedSelect = $('#data-directed');

  if (!loadButton || !pluginSelect || !modal || !closeBtn || !cancelBtn || !confirmBtn || !sourceSelect || !filePresetSelect || !fileInput || !directedSelect) {
    return;
  }

  const closeModal = () => modal.classList.remove('open');
  const openModal = () => modal.classList.add('open');
  const presetValues = new Set(
    Array.from(filePresetSelect.options)
      .map(option => option.value)
      .filter(value => value && value !== '__custom__')
  );

  const syncPresetFromFile = () => {
    const fileValue = fileInput.value.trim();
    filePresetSelect.value = presetValues.has(fileValue) ? fileValue : '__custom__';
  };

  loadButton.addEventListener('click', () => {
    if (!state.activePlugin) {
      pluginSelect.focus();
      showToast('Select a plugin first', 'info');
      return;
    }
    syncPresetFromFile();
    openModal();
  });

  closeBtn.addEventListener('click', closeModal);
  cancelBtn.addEventListener('click', closeModal);
  modal.addEventListener('click', (event) => {
    if (event.target === modal) {
      closeModal();
    }
  });

  filePresetSelect.addEventListener('change', () => {
    if (filePresetSelect.value === '__custom__') {
      fileInput.focus();
      return;
    }
    fileInput.value = filePresetSelect.value;
  });

  fileInput.addEventListener('input', syncPresetFromFile);

  confirmBtn.addEventListener('click', async () => {
    const source = sourceSelect.value.trim();
    const file = fileInput.value.trim();
    const directed = directedSelect.value;

    if (!file) {
      showToast('Enter a file path', 'error');
      return;
    }

    confirmBtn.disabled = true;
    loadButton.disabled = true;
    pluginSelect.disabled = true;

    try {
      const params = new URLSearchParams({
        plugin: state.activePlugin,
        source,
        file,
        directed,
      });
      const response = await fetch(`/load-plugin/?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.load_error || 'Graph data could not be loaded.');
      }
      applyPluginResponse(data);
      history.replaceState({}, '', '/');
      closeModal();
      termPrint(`info Loaded data for ${state.activePlugin}`, 'info');
      showToast('Graph loaded', 'success');
    } catch (error) {
      termPrint(`error ${error.message}`, 'error');
      showToast(error.message, 'error');
    } finally {
      confirmBtn.disabled = false;
      loadButton.disabled = false;
      pluginSelect.disabled = false;
    }
  });
}

function setupPredefinedLoader() {
  const predefinedBtn = $('#btn-load-predefined');

  if (!predefinedBtn) return;

  predefinedBtn.addEventListener('click', () => {
    const params = new URLSearchParams({
      plugin: 'simple-visualizer',
      source: 'json-data-source',
      file: 'json_data_source/json_data_source/data/demo_mixed_small.json',
      directed: 'true',
    });
    window.location.href = `/?${params.toString()}`;
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
  state.activePlugin = bootstrap.visualizerName || '';
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
  setPluginUiVisible(true);
  updateGraphStats(graph);
  const overlay = $('#canvas-overlay');
  if (overlay) {
    overlay.classList.add('hidden');
  }

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
  setPluginUiVisible(false);
  updateGraphStats(null);

  if (window.GVIZ_ACTIVE_VISUALIZER && typeof window.GVIZ_ACTIVE_VISUALIZER.clear === 'function') {
    window.GVIZ_ACTIVE_VISUALIZER.clear();
  }

  const overlay = $('#canvas-overlay');
  if (overlay) {
    overlay.classList.remove('hidden');
  }
}

function setPluginUiVisible(visible) {
  document.querySelectorAll('[data-plugin-only]').forEach((el) => {
    el.hidden = !visible;
  });
}

function unloadPlugin() {
  state.originalGraph = null;
  state.activePlugin = '';
  const pluginSelect = $('#plugin-select');
  if (pluginSelect) {
    pluginSelect.value = '';
  }
  const workspaceName = $('#workspace-name');
  if (workspaceName) {
    workspaceName.textContent = 'No Workspace';
  }
  if (window.GVIZ_ACTIVE_VISUALIZER && typeof window.GVIZ_ACTIVE_VISUALIZER.clear === 'function') {
    window.GVIZ_ACTIVE_VISUALIZER.clear();
  }
  window.GVIZ_PLUGIN_BOOTSTRAP = null;
  window.GVIZ_ACTIVE_VISUALIZER = null;
  showEmptyGraph();
}

function applyPluginResponse(data) {
  const workspaceName = $('#workspace-name');
  if (workspaceName) {
    workspaceName.textContent = data.workspace_name || 'Workspace';
  }

  const pluginSelect = $('#plugin-select');
  if (pluginSelect) {
    pluginSelect.value = data.plugin_name || state.activePlugin || '';
  }

  installVisualizerRuntime(data.visualizer_html || '');
  const bootstrap = window.GVIZ_PLUGIN_BOOTSTRAP;
  if (!bootstrap || !bootstrap.graph) {
    throw new Error('Visualizer runtime did not provide graph bootstrap data.');
  }

  state.originalGraph = cloneGraph(bootstrap.graph);
  state.activePlugin = data.plugin_name || bootstrap.visualizerName || '';
  setGraph(cloneGraph(bootstrap.graph));
}

function installVisualizerRuntime(html) {
  if (window.GVIZ_ACTIVE_VISUALIZER && typeof window.GVIZ_ACTIVE_VISUALIZER.clear === 'function') {
    window.GVIZ_ACTIVE_VISUALIZER.clear();
  }
  window.GVIZ_PLUGIN_BOOTSTRAP = null;
  window.GVIZ_ACTIVE_VISUALIZER = null;

  const host = document.createElement('div');
  host.innerHTML = html.trim();
  const scriptNode = host.querySelector('script');
  if (!scriptNode) {
    throw new Error('Visualizer response did not include runtime script.');
  }

  const runtimeScript = document.createElement('script');
  runtimeScript.textContent = scriptNode.textContent;
  document.body.appendChild(runtimeScript);
  runtimeScript.remove();
}

function updateGraphStats(graph) {
  const nodeCount = $('#stat-node-count');
  const edgeCount = $('#stat-edge-count');
  const graphKind = $('#stat-graph-kind');
  if (!nodeCount || !edgeCount || !graphKind) return;

  nodeCount.textContent = graph ? graph.nodes.length : '0';
  edgeCount.textContent = graph ? graph.edges.length : '0';
  graphKind.textContent = graph
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

  if (!searchInput || !filterInput || !searchBtn || !filterBtn || !resetBtn) {
    return;
  }

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
  const terminalPanel = document.querySelector('.terminal-panel');
  if (!input || !terminalPanel) return;
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

  terminalPanel.addEventListener('click', () => input.focus());
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
  if (!output) return;
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
