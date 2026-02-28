# JSONDataSourcePlugin implementation.
from __future__ import annotations

import os
from typing import Any, List

from api.exceptions import ParseError
from api.models import Graph
from api.plugins import DataSourcePlugin, PluginParameter
from json_data_source.parser import JSONParser


class JSONDataSourcePlugin(DataSourcePlugin):
    """Data-source plugin that parses arbitrary JSON files"""

    # DataSourcePlugin ABC
    def get_name(self) -> str:
        return "json-data-source"

    def get_description(self) -> str:
        return (
            "Parses an arbitrary JSON file and constructs a graph.  "
            "Supports cyclic structures via @id/@ref semantics: any string "
            "value that matches the @id of another JSON object is resolved "
            "as a directed edge rather than a plain attribute."
        )

    def get_parameters(self) -> List[PluginParameter]:
        return [
            PluginParameter(
                name="file_path",
                label="JSON file path",
                description=(
                    "Absolute or relative path to the JSON file.  "
                    "The file must be UTF-8 encoded and contain valid JSON."
                ),
                required=True,
                param_type=str,
            ),
            PluginParameter(
                name="directed",
                label="Directed graph",
                description=(
                    "Set to 'true' to treat the graph as directed (default), "
                    "or 'false' for an undirected graph."
                ),
                required=False,
                default="true",
                param_type=str,
            ),
        ]

    def load(self, **kwargs: Any) -> Graph:
        """Parse the JSON file specified by *file_path* and return a graph"""
        file_path: str = kwargs.get("file_path", "")
        if not file_path:
            raise ParseError("<missing>", "Parameter 'file_path' is required")

        # Resolve relative paths against the current working directory
        file_path = os.path.abspath(file_path)

        directed_raw: str = str(kwargs.get("directed", "true")).strip().lower()
        directed: bool = directed_raw not in ("false", "0", "no")

        parser = JSONParser(directed=directed)
        graph = parser.parse_file(file_path, directed=directed)
        return graph

    def __repr__(self) -> str:
        return "JSONDataSourcePlugin()"
