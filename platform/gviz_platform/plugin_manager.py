# Plugin discovery and registry

from __future__ import annotations

import importlib.metadata
import logging
from typing import Dict, List, Optional

from api.plugins import (
    DATA_SOURCE_ENTRY_POINT_GROUP,
    DataSourcePlugin,
    VISUALIZER_ENTRY_POINT_GROUP,
    VisualizerPlugin,
)

logger = logging.getLogger(__name__)


class PluginManager:
    """Discovers, loads, and provides access to all installed gviz plugins"""

    def __init__(self) -> None:
        self._data_sources: Dict[str, DataSourcePlugin] = {}
        self._visualizers: Dict[str, VisualizerPlugin] = {}
        self._discovered: bool = False

    # Discovery
    def discover(self) -> None:
        """Scan installed packages for gviz plugins and register them"""
        self._data_sources = {}
        self._visualizers = {}

        self._discover_group(
            group=DATA_SOURCE_ENTRY_POINT_GROUP,
            registry=self._data_sources,
            expected_type=DataSourcePlugin,
            label="data-source",
        )
        self._discover_group(
            group=VISUALIZER_ENTRY_POINT_GROUP,
            registry=self._visualizers,
            expected_type=VisualizerPlugin,
            label="visualizer",
        )
        self._discovered = True
        logger.info(
            "Plugin discovery complete – %d data-source(s), %d visualizer(s) found.",
            len(self._data_sources),
            len(self._visualizers),
        )

    def _discover_group(
        self,
        group: str,
        registry: Dict,
        expected_type: type,
        label: str,
    ) -> None:
        try:
            eps = importlib.metadata.entry_points(group=group)
        except Exception as exc:
            logger.warning("Could not query entry points for group '%s': %s", group, exc)
            return

        for ep in eps:
            try:
                plugin_class = ep.load()
                instance = plugin_class()
                if not isinstance(instance, expected_type):
                    logger.warning(
                        "Entry point '%s' in group '%s' does not implement %s – skipped.",
                        ep.name,
                        group,
                        expected_type.__name__,
                    )
                    continue
                registry[instance.get_name()] = instance
                logger.debug("Loaded %s plugin: '%s'", label, instance.get_name())
            except Exception as exc:
                logger.warning(
                    "Failed to load %s plugin from entry point '%s': %s",
                    label,
                    ep.name,
                    exc,
                )

    # Data-source plugin access
    def get_data_source(self, name: str) -> Optional[DataSourcePlugin]:
        """Return the data-source plugin registered under name, or `None`"""
        self._ensure_discovered()
        return self._data_sources.get(name)

    def list_data_sources(self) -> List[DataSourcePlugin]:
        """Return all registered data-source plugins"""
        self._ensure_discovered()
        return sorted(self._data_sources.values(), key=lambda p: p.get_name())

    # Visualizer plugin access
    def get_visualizer(self, name: str) -> Optional[VisualizerPlugin]:
        """Return the visualiser plugin registered under name, or `None`"""
        self._ensure_discovered()
        return self._visualizers.get(name)

    def list_visualizers(self) -> List[VisualizerPlugin]:
        """Return all registered visualiser plugins"""
        self._ensure_discovered()
        return sorted(self._visualizers.values(), key=lambda p: p.get_name())

    # Internal helpers
    def _ensure_discovered(self) -> None:
        if not self._discovered:
            self.discover()

    def __repr__(self) -> str:
        return (
            f"PluginManager("
            f"data_sources={list(self._data_sources.keys())}, "
            f"visualizers={list(self._visualizers.keys())})"
        )
