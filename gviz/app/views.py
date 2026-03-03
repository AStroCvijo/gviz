from __future__ import annotations

from pathlib import Path

from django.apps import apps
from django.shortcuts import render


def index(request):
    """Main graph explorer view"""
    context = {
        "workspace_name": "No Workspace",
        "initial_graph_loaded": False,
        "node_count": 0,
        "edge_count": 0,
        "graph_kind_label": "no graph",
        "visualizer_html": "",
        "load_error": "",
    }

    plugin_name = request.GET.get("plugin", "").strip()
    source_name = request.GET.get("source", "").strip()
    file_path = request.GET.get("file", "").strip()

    if plugin_name and not source_name:
        source_name = "json-data-source"
    if plugin_name and not file_path:
        file_path = "json_data_source/json_data_source/data/social_network.json"

    if not plugin_name:
        return render(request, "app/index.html", context)

    app_config = apps.get_app_config("app")
    plugin_manager = getattr(app_config, "plugin_manager", None)
    if plugin_manager is None:
        context["load_error"] = "Plugin manager is not available."
        return render(request, "app/index.html", context)

    data_source = plugin_manager.get_data_source(source_name)
    visualizer = plugin_manager.get_visualizer(plugin_name)
    if data_source is None or visualizer is None:
        context["load_error"] = "Requested plugin could not be found."
        return render(request, "app/index.html", context)

    repo_root = Path(__file__).resolve().parents[2]
    resolved_path = Path(file_path)
    if not resolved_path.is_absolute():
        resolved_path = repo_root / resolved_path

    directed = request.GET.get("directed", "true")

    try:
        graph = data_source.load(file_path=str(resolved_path), directed=directed)
        context.update(
            workspace_name=Path(file_path).stem.replace("_", " ").title(),
            initial_graph_loaded=True,
            node_count=graph.node_count(),
            edge_count=graph.edge_count(),
            graph_kind_label="directed" if graph.is_directed() else "undirected",
            visualizer_html=visualizer.render(graph),
        )
    except Exception as exc:
        context["load_error"] = str(exc)

    return render(request, "app/index.html", context)
