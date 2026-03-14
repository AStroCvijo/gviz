/* ============================================================
   gviz — UI shell
   Student 2 visualizer logic is provided by the selected plugin.
   ============================================================ */

'use strict';

const state = {
  selectedNodeId: null,
  graph: null,
  originalGraph: null,
  filter: {filters: []},
  activePlugin: '',
  workspace: (new URLSearchParams(window.location.search)).get("workspace"),
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
  setupResizers();
  bootGraph();
});

function setupWorkspaceTabs() {
  $$('.ws-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      if (e.target.closest('.ws-close')) return;
      $$('.ws-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      openWorkspace(tab.getAttribute("id"))
    });

    const closeBtn = tab.querySelector('.ws-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', async(e) => {
        try {
          const response = await fetch(`/workspace/${tab.getAttribute("id")}`, {
            method: "DELETE",
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
          });
          const data = await response.json();
          if (!response.ok || !data.ok) {
            throw new Error(data.load_error || 'Workspace could not be created.');
          }
          if (tab.getAttribute("id") === state.workspace)
            openWorkspace()
          applyPluginResponse(data)
        } catch (error) {
          showToast(error.message, 'error');
        };
      });
    }
  });

  $('#ws-tab-add').addEventListener("click", async () => {
    try {
      const response = await fetch(`/workspace/`, {
        method: "POST",
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.load_error || 'Workspace could not be created.');
      }
      openWorkspace(data.workspace_id)
    } catch (error) {
      showToast(error.message, 'error');
    }
  })
}

function setupPluginSelection() {
  const pluginSelect = $('#plugin-select');
  const loadButton = $('#btn-load-data');

  if (!pluginSelect || !loadButton) return;

  pluginSelect.addEventListener('change', async () => {
    const plugin = pluginSelect.value;
    if (!plugin) {
      unloadPlugin();
      return;
    }

    state.activePlugin = plugin;
    try {
      const params = new URLSearchParams({
        workspace: state.workspace,
        plugin: state.activePlugin,
      });
      const response = await fetch(`/load-plugin/?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.load_error || 'Plugin could not be loaded.');
      }
      applyPluginResponse(data);
      termPrint(`info Selected ${plugin}.`, 'info');
      showToast('Plugin selected', 'info');
    } catch (error) {
      termPrint(`error ${error.message}`, 'error');
      showToast(error.message, 'error');
    }
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
  const syncFileInputMode = () => {
    const isCustom = filePresetSelect.value === '__custom__';
    fileInput.readOnly = !isCustom;
    fileInput.setAttribute('aria-readonly', String(!isCustom));
  };

  const syncPresetFromFile = () => {
    const fileValue = fileInput.value.trim();
    filePresetSelect.value = presetValues.has(fileValue) ? fileValue : '__custom__';
    syncFileInputMode();
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
      syncFileInputMode();
      fileInput.focus();
      return;
    }
    fileInput.value = filePresetSelect.value;
    if (filePresetSelect.value.endsWith('.xml')) {
      sourceSelect.value = 'xml-data-source';
    } else if (filePresetSelect.value.endsWith('.json')) {
      sourceSelect.value = 'json-data-source';
    }
    syncFileInputMode();
  });

  fileInput.addEventListener('input', syncPresetFromFile);
  syncPresetFromFile();

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
        workspace: state.workspace,
        source,
        file,
        directed,
      });
      const response = await fetch(`/load-graph/?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.load_error || 'Graph data could not be loaded.');
      }
      applyPluginResponse(data);
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

  predefinedBtn.addEventListener('click', async () => {
    try {
      let params = new URLSearchParams({
        workspace: state.workspace,
        plugin: 'simple-visualizer',
      });
      let response = await fetch(`/load-plugin/?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      let data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.load_error || 'Graph data could not be loaded.');
      }
      applyPluginResponse(data);
      termPrint(`info Selected ${data.plugin_name}.`, 'info');
      showToast('Plugin selected', 'info');

      params = new URLSearchParams({
        workspace: state.workspace,
        source: 'json-data-source',
        file: 'json_data_source/json_data_source/data/demo_mixed_small.json',
        directed: 'true',
      });
      response = await fetch(`/load-graph/?${params.toString()}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
      });
      data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.load_error || 'Graph data could not be loaded.');
      }
      applyPluginResponse(data);
      termPrint(`info Loaded data for ${state.activePlugin}`, 'info');
      showToast('Graph loaded', 'success');
    } catch (error) {
      termPrint(`error ${error.message}`, 'error');
      showToast(error.message, 'error');
    }
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
  if (window.GVIZ_ACTIVE_VISUALIZER && typeof window.GVIZ_ACTIVE_VISUALIZER.clear === 'function') {
    window.GVIZ_ACTIVE_VISUALIZER.clear();
  }
  window.GVIZ_PLUGIN_BOOTSTRAP = null;
  window.GVIZ_ACTIVE_VISUALIZER = null;
  showEmptyGraph();
}

function applyPluginResponse(data) {
  if (data.workspace_id)
    state.workspace = data.workspace_id

  if (data.workspaces) {
    const workspace_tabs = $('#workspace-tabs')
    if (workspace_tabs) {
      workspace_tabs.innerHTML = ""
      for (let workspace of data.workspaces) {
        workspace_tabs.innerHTML += `
        <div class="ws-tab ${workspace.workspace_id === state.workspace ? "active" : ""}" id="${workspace.workspace_id}">
          <span class="ws-dot"></span>
          <span class="workspace-name">${workspace.name}</span>
          <span class="ws-close">✕</span>
        </div>
      `
      }
      workspace_tabs.innerHTML += `<div class="ws-tab-add" id="ws-tab-add">+</div>`
      setupWorkspaceTabs();
    }
  }

  const viewMode = $('#view-mode')
  viewMode.innerText = data.plugin_name === "simple-visualizer" ? "Simple" : data.plugin_name === "block-visualizer" ? "Block" : "Custom"

  const pluginSelect = $('#plugin-select');
  if (pluginSelect) {
    pluginSelect.value = data.plugin_name || state.activePlugin || '';
  }

  if (data.filter)
    state.filter = data.filter;

  if (data.visualizer_html) {
    installVisualizerRuntime(data.visualizer_html || '');
    const bootstrap = window.GVIZ_PLUGIN_BOOTSTRAP;
    if (!bootstrap || !bootstrap.graph) {
      throw new Error('Visualizer runtime did not provide graph bootstrap data.');
    }

    state.originalGraph = cloneGraph(bootstrap.graph);
    state.activePlugin = data.plugin_name || bootstrap.visualizerName || '';
    setGraph(cloneGraph(bootstrap.graph));
  }

  if (data.output)
    termPrint(data.output, "muted")
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

function setupResizers() {
  const root = document.documentElement;

  const treeResizer = $('#resizer-tree');
  if (treeResizer) {
    let startX, startW;
    treeResizer.addEventListener('mousedown', e => {
      startX = e.clientX;
      startW = parseInt(getComputedStyle(root).getPropertyValue('--tree-w'));
      treeResizer.classList.add('dragging');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      const onMove = e => {
        const w = Math.max(120, Math.min(520, startW + e.clientX - startX));
        root.style.setProperty('--tree-w', w + 'px');
      };
      const onUp = () => {
        treeResizer.classList.remove('dragging');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      };
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
  }

  const termResizer = $('#resizer-terminal');
  if (termResizer) {
    let startY, startH;
    termResizer.addEventListener('mousedown', e => {
      startY = e.clientY;
      startH = parseInt(getComputedStyle(root).getPropertyValue('--terminal-h'));
      termResizer.classList.add('dragging');
      document.body.style.cursor = 'row-resize';
      document.body.style.userSelect = 'none';
      const onMove = e => {
        const h = Math.max(36, Math.min(480, startH - (e.clientY - startY)));
        root.style.setProperty('--terminal-h', h + 'px');
      };
      const onUp = () => {
        termResizer.classList.remove('dragging');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      };
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
  }
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
    console.log(filterInput.value.trim())
    if (e.key === 'Enter') doFilter(filterInput.value.trim());
  });

  resetBtn.addEventListener('click', async () => {
    searchInput.value = '';
    filterInput.value = '';
    if (!state.originalGraph) {
      showToast('No graph loaded', 'error');
      return;
    }

    state.filter = {search: "", filters: []}
    termPrint('$ filter --reset', 'cmd');
    await sendFilterRequest()
    termPrint('  ✓ Workspace reset to original graph', 'info');
    showToast('Graph reset', 'info');
    setGraph(cloneGraph(state.originalGraph));
  });
}

async function doSearch(query) {
  if (!query && query !== "") return;
  if (!state.graph) {
    showToast('No graph loaded', 'error');
    return;
  }

  termPrint(`$ search ${query}`, 'cmd');
  state.filter.search = query;
  if (await sendFilterRequest()) {
    showToast(`Search: ${state.graph.nodes.length} nodes found`, 'success');
    termPrint(`Search: ${state.graph.nodes.length} nodes found`, 'muted')
  }
}

async function doFilter(expr) {
  if (!expr) return;
  if (!state.graph) {
    showToast('No graph loaded', 'error');
    return;
  }

  termPrint(`$ filter ${expr}`, 'cmd');
  state.filter.filters.push(expr);
  if (await sendFilterRequest()) {
    showToast(`Filter: ${state.graph.nodes.length} nodes found`, 'success');
    termPrint(`Filter: ${state.graph.nodes.length} nodes found`, 'muted')
  }
  else
    state.filter.filters.pop();
}

async function sendFilterRequest() {
  try {
    const response = await fetch(`/workspace/${state.workspace}/filter/`, {
      method: "POST",
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body: JSON.stringify(state.filter)
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.load_error || 'Workspace could not be created.');
    }
    applyPluginResponse(data)
    return true
  } catch (error) {
    showToast(error.message, 'error');
    return false
  }
}

function openWorkspace(workspace_id = "") {
  const url = new URL(window.location.href)
  if (!workspace_id) {
    url.search = ""
    window.location.href = url.href
  }
  else {
    state.workspace = workspace_id
    url.searchParams.set("workspace", workspace_id)
    url.search = url.searchParams.toString()
    window.location.href = url.href
  }
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

async function handleTermCommand(cmd) {
  termPrint(`gviz > ${cmd}`, 'cmd');
  const parts = cmd.trim().split(/\s+/);
  const verb = parts[0].toLowerCase();

  if (verb === 'clear') {
    $('#term-output').innerHTML = '';
    return;
  }

  try {
    const response = await fetch(`/workspace/${state.workspace}/cli/`, {
      method: "POST",
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      body: cmd
    });
    const data = await response.json();
    if (!data.ok) {
      showToast(data.load_error, 'error');
      termPrint(data.load_error, "error")
    }
    applyPluginResponse(data)
  } catch (error) {
    showToast(error.message, 'error');
    termPrint(error.message, "error")
  }
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
