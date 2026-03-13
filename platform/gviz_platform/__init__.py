"""
gviz_platform — Graph Visualizer Platform core library.

This package provides:

* Concrete implementations of the :class:`~api.models.Graph`, :class:`~api.models.Node`
  and :class:`~api.models.Edge` ABCs defined in ``gviz-api``.
* A :class:`~gviz_platform.plugin_manager.PluginManager` that auto-discovers
  all installed data-source and visualiser plugins via Python entry points.
* A :class:`~gviz_platform.workspace.WorkspaceManager` that manages multiple
  simultaneously loaded graphs (workspaces).
* A :class:`~gviz_platform.filter_engine.FilterEngine` that implements graph
  search and attribute filtering.

The platform is framework-agnostic: it can be used from Django, Flask, or
a plain Python script / CLI without modification.
"""

from gviz_platform.graph import ConcreteGraph, ConcreteNode, ConcreteEdge
from gviz_platform.plugin_manager import PluginManager
from gviz_platform.workspace import WorkspaceManager, Workspace
from gviz_platform.filter_engine import FilterEngine
from gviz_platform.cli_handler import CLIHandler

__all__ = [
    "ConcreteGraph",
    "ConcreteNode",
    "ConcreteEdge",
    "PluginManager",
    "WorkspaceManager",
    "Workspace",
    "FilterEngine",
    "CLIHandler"
]
