# Workspace management.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from api.models import Graph

# Workspace
@dataclass
class Workspace:
    """Represents a single loaded graph with its active state"""
    workspace_id: str
    name: str
    plugin_name: str
    plugin_params: Dict
    original_graph: Graph
    current_graph: Graph = field(init=False)
    applied_operations: List[Dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.current_graph = self.original_graph

    # State mutation
    def apply_filter(self, expression: str, result_graph: Graph) -> None:
        """Record a filter operation and update the current graph"""
        self.applied_operations.append({"type": "filter", "query": expression})
        self.current_graph = result_graph

    def apply_search(self, query: str, result_graph: Graph) -> None:
        """Record a search operation and update the current graph"""
        self.applied_operations.append({"type": "search", "query": query})
        self.current_graph = result_graph

    def reset(self) -> None:
        """Discard all filter/search operations and restore the original graph."""
        self.applied_operations.clear()
        self.current_graph = self.original_graph

    # Serialisation helper (for UI rendering)
    def to_dict(self) -> Dict:
        """Return a serialisable summary of this workspace."""
        return {
            "workspace_id": self.workspace_id,
            "name": self.name,
            "plugin_name": self.plugin_name,
            "node_count": self.current_graph.node_count(),
            "edge_count": self.current_graph.edge_count(),
            "operations": list(self.applied_operations),
        }

    def __repr__(self) -> str:
        return (
            f"Workspace(id={self.workspace_id!r}, name={self.name!r}, "
            f"plugin={self.plugin_name!r}, ops={len(self.applied_operations)})"
        )

# WorkspaceManager
class WorkspaceManager:
    """Manages the collection of open workspaces for the current session"""

    def __init__(self) -> None:
        self._workspaces: Dict[str, Workspace] = {}
        self._active_id: Optional[str] = None

    # CRUD
    def create_workspace(
        self,
        name: str,
        plugin_name: str,
        plugin_params: Dict,
        graph: Graph,
    ) -> Workspace:
        """Create a new workspace and register it"""
        workspace_id = str(uuid.uuid4())
        workspace = Workspace(
            workspace_id=workspace_id,
            name=name,
            plugin_name=plugin_name,
            plugin_params=dict(plugin_params),
            original_graph=graph,
        )
        self._workspaces[workspace_id] = workspace
        if self._active_id is None:
            self._active_id = workspace_id
        return workspace

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Return the workspace with *workspace_id*, or ``None``."""
        return self._workspaces.get(workspace_id)

    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace by id"""
        if workspace_id not in self._workspaces:
            return False
        del self._workspaces[workspace_id]
        if self._active_id == workspace_id:
            # Promote the most recently created remaining workspace, if any.
            remaining = list(self._workspaces.keys())
            self._active_id = remaining[-1] if remaining else None
        return True

    # Active workspace
    def get_active_workspace(self) -> Optional[Workspace]:
        """Return the currently active workspace, or `None`"""
        if self._active_id is None:
            return None
        return self._workspaces.get(self._active_id)

    def set_active_workspace(self, workspace_id: str) -> bool:
        """Make the workspace with workspace_id the active one"""
        if workspace_id not in self._workspaces:
            return False
        self._active_id = workspace_id
        return True

    # Listing
    def list_workspaces(self) -> List[Workspace]:
        """Return all workspaces, ordered by creation time (oldest first)."""
        return list(self._workspaces.values())

    def workspace_count(self) -> int:
        """Return the number of open workspaces."""
        return len(self._workspaces)

    def __repr__(self) -> str:
        return (
            f"WorkspaceManager("
            f"count={len(self._workspaces)}, "
            f"active={self._active_id!r})"
        )
