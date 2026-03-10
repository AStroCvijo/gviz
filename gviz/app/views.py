from __future__ import annotations

from nis import cat
from pathlib import Path
import json

from django.apps import apps
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views.decorators.csrf import csrf_exempt

from api import Graph, FilterError
from gviz_platform import Workspace


def _load_visualizer_context(workspace_id: str):
    context = {
        "workspace_name": "No Workspace",
        "workspace_id": "",
        "workspaces": [],
        "workspace_count": 0,
        "visualization_plugins": [],
        "initial_graph_loaded": False,
        "node_count": 0,
        "edge_count": 0,
        "graph_kind_label": "no graph",
        "visualizer_html": "",
        "load_error": "",
        "plugin_name": "",
        "filter": {"filters":[]},
    }

    app_config = apps.get_app_config("app")
    workspace_manager = getattr(app_config, "workspace_manager", None)
    if workspace_manager:
        if len(workspace_manager.list_workspaces()) == 0:
            workspace_manager = getattr(app_config, "workspace_manager", None)
            workspace_manager.create_workspace()

        context["workspaces"] = [{"name": w.name, "workspace_id": w.workspace_id} for w in workspace_manager.list_workspaces()]
        context["workspace_count"] = len(context["workspaces"])

    workspace = next((w for w in workspace_manager.list_workspaces() if w.workspace_id == workspace_id), workspace_manager.list_workspaces()[0])
    context["workspace_name"] = workspace.name
    context["workspace_id"] = workspace.workspace_id

    search =  next((o["query"] for o in workspace.applied_operations if o["type"] == "search"), None)
    if search != None:
        context["filter"]["search"] = search
    context["filter"]["filters"] = [o["query"] for o in workspace.applied_operations if o["type"] == "filter"]
    plugin_name = workspace.plugin_name

    plugin_manager = getattr(app_config, "plugin_manager", None)
    if plugin_manager is None:
        context["load_error"] = "Plugin manager is not available."
        return context

    for visualizer in plugin_manager.list_visualizers():
        context["visualization_plugins"].append(
            {"name": visualizer.get_name(), "text": visualizer.get_name().replace("-", " ").title()})

    if not plugin_name:
        return context

    visualizer = plugin_manager.get_visualizer(plugin_name)
    if visualizer is None:
        context["load_error"] = "Requested plugin could not be found."
        return context

    context.update(
        plugin_name=plugin_name,
    )
    if (workspace.current_graph != None):
        context.update(
            initial_graph_loaded=True,
            node_count=workspace.current_graph.node_count(),
            edge_count=workspace.current_graph.edge_count(),
            graph_kind_label="directed" if workspace.current_graph.is_directed() else "undirected",
            visualizer_html=visualizer.render(workspace.current_graph),
        )
    return context


def _load_graph_from_source(source_name: str, file_path: str, directed: bool):
    app_config = apps.get_app_config("app")
    plugin_manager = getattr(app_config, "plugin_manager", None)
    data_source = plugin_manager.get_data_source(source_name)
    if data_source is None:
        return None, "Requested data source plugin could not be found."

    repo_root = Path(__file__).resolve().parents[2]
    resolved_path = Path(file_path)
    if not resolved_path.is_absolute():
        resolved_path = repo_root / resolved_path

    try:
        return data_source.load(file_path=str(resolved_path), directed=directed), ""
    except Exception as exc:
        return None, str(exc)

def index(request):
    """Main graph explorer view"""
    workspace_id = request.GET.get("workspace", "").strip()
    context = _load_visualizer_context(workspace_id)

    if context["workspace_id"] != workspace_id:
        return redirect(reverse("index") + f"?workspace={context['workspace_id']}")

    return render(request, "app/index.html", context)


def load_plugin(request):
    workspace_id = request.GET.get("workspace", "").strip()
    plugin_name = request.GET.get("plugin", "").strip()

    app_config = apps.get_app_config("app")
    workspace_manager = getattr(app_config, "workspace_manager", None)
    workspace = workspace_manager.get_workspace(workspace_id)

    workspace.plugin_name = plugin_name

    context = _load_visualizer_context(workspace_id)
    status = 200 if context["plugin_name"] == plugin_name == workspace.plugin_name else 400
    return JsonResponse(
        {
            "ok": status == 200,
            "workspace_name": context["workspace_name"],
            "workspace_id": context["workspace_id"],
            "workspaces": context["workspaces"],
            "plugin_name": context["plugin_name"],
            "node_count": context["node_count"],
            "edge_count": context["edge_count"],
            "graph_kind_label": context["graph_kind_label"],
            "visualizer_html": context["visualizer_html"],
            "load_error": context["load_error"],
            "filter": context["filter"],
        },
        status=status,
    )

def load_graph(request):
    workspace_id = request.GET.get("workspace", "").strip()
    source_name = request.GET.get("source", "").strip()
    file_path = request.GET.get("file", "").strip()
    directed = request.GET.get("directed", "true")

    app_config = apps.get_app_config("app")
    workspace_manager = getattr(app_config, "workspace_manager", None)
    workspace =  workspace_manager.get_workspace(workspace_id)

    graph, error = _load_graph_from_source(source_name, file_path, directed)
    workspace.original_graph = graph
    workspace.current_graph = graph
    if error == "":
        workspace.name = Path(file_path).stem.replace("_", " ").title()

    context = _load_visualizer_context(workspace_id)
    status = 200 if context["initial_graph_loaded"] else 400
    return JsonResponse(
        {
            "ok": context["initial_graph_loaded"],
            "workspace_name": context["workspace_name"],
            "workspace_id": context["workspace_id"],
            "workspaces": context["workspaces"],
            "plugin_name": context["plugin_name"],
            "node_count": context["node_count"],
            "edge_count": context["edge_count"],
            "graph_kind_label": context["graph_kind_label"],
            "visualizer_html": context["visualizer_html"],
            "load_error": context["load_error"] if context["load_error"] != "" else error,
            "filter": context["filter"],
        },
        status=status,
    )

@csrf_exempt
def create_workspace(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "load_error": "Method not allowed"}, status=405)

    app_config = apps.get_app_config("app")
    workspace_manager = getattr(app_config, "workspace_manager", None)
    new_workspace = workspace_manager.create_workspace()

    context = _load_visualizer_context(new_workspace.workspace_id)
    status = 200 if context["workspace_id"] == new_workspace.workspace_id else 400
    return JsonResponse(
        {
            "ok": status == 200,
            "workspace_name": context["workspace_name"],
            "workspace_id": context["workspace_id"],
            "workspaces": context["workspaces"],
            "plugin_name": context["plugin_name"],
            "node_count": context["node_count"],
            "edge_count": context["edge_count"],
            "graph_kind_label": context["graph_kind_label"],
            "visualizer_html": context["visualizer_html"],
            "load_error": context["load_error"],
            "filter": context["filter"],
        },
        status=status,
    )

@csrf_exempt
def delete_workspace(request, workspace_id):
    if request.method != "DELETE":
        return JsonResponse({"ok": False, "load_error": "Method not allowed"}, status=405)

    app_config = apps.get_app_config("app")
    workspace_manager = getattr(app_config, "workspace_manager", None)
    workspace_manager.delete_workspace(workspace_id)

    return JsonResponse(
        {
            "ok": True,
            "workspaces": [{"name": w.name, "workspace_id": w.workspace_id} for w in workspace_manager.list_workspaces()]
        },
        status=200,
    )

@csrf_exempt
def filter(request, workspace_id):
    app_config = apps.get_app_config("app")
    workspace_manager = getattr(app_config, "workspace_manager", None)
    workspace = workspace_manager.get_workspace(workspace_id)

    body = json.loads(request.body.decode("utf-8"))
    filter_engine = getattr(app_config, "filter_engine", None)
    if "search" in body:
        workspace.applied_operations = [o for o in workspace.applied_operations if o["type"] != "search"]
        workspace.apply_search(body["search"], filter_engine.search(workspace.original_graph, body["search"]))
    try:
        if "filters" in body:
            workspace.applied_operations = [o for o in workspace.applied_operations if o["type"] != "filter"]
            for filter in body["filters"]:
                workspace.apply_filter(filter, filter_engine.filter(workspace.current_graph, filter))
    except FilterError as err:
        return JsonResponse({"ok": False, "load_error": str(err)}, status=400)

    context = _load_visualizer_context(workspace.workspace_id)
    status = 200 if context["workspace_id"] == workspace.workspace_id else 400
    return JsonResponse(
        {
            "ok": status == 200,
            "workspace_name": context["workspace_name"],
            "workspace_id": context["workspace_id"],
            "workspaces": context["workspaces"],
            "plugin_name": context["plugin_name"],
            "node_count": context["node_count"],
            "edge_count": context["edge_count"],
            "graph_kind_label": context["graph_kind_label"],
            "visualizer_html": context["visualizer_html"],
            "load_error": context["load_error"],
            "filter": context["filter"],
        },
        status=status,
    )

@csrf_exempt
def update_nodes(request, workspace_id, node_id):
    app_config = apps.get_app_config("app")
    workspace_manager = getattr(app_config, "workspace_manager", None)
    workspace = workspace_manager.get_workspace(workspace_id)

    if request.method == "POST":
        pass
    elif request.method == "DELETE":
        pass
    elif request.method == "PUT":
        pass

@csrf_exempt
def update_edges(request, workspace_id, edge_id):
    app_config = apps.get_app_config("app")
    workspace_manager = getattr(app_config, "workspace_manager", None)
    workspace = workspace_manager.get_workspace(workspace_id)

    if request.method == "POST":
        pass
    elif request.method == "DELETE":
        pass
    elif request.method == "PUT":
        pass
