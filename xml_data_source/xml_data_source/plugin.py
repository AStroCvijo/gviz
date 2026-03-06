from __future__ import annotations

import os
from typing import Any, List

from api.exceptions import ParseError
from api.models import Graph
from api.plugins import DataSourcePlugin, PluginParameter
from xml_data_source.parser import XMLParser


class XMLDataSourcePlugin(DataSourcePlugin):

    def get_name(self) -> str:
        return "xml-data-source"

    def get_description(self) -> str:
        return (
            "Parses an arbitrary XML file and constructs a graph.  "
            "Each XML element becomes a node with its attributes and text content.  "
            "Supports cyclic structures via ref semantics: any element with a "
            "ref attribute pointing to the id of another element is resolved "
            "as a directed edge rather than a new node."
        )

    def get_parameters(self) -> List[PluginParameter]:
        return [
            PluginParameter(
                name="file_path",
                label="XML file path",
                description=(
                    "Absolute or relative path to the XML file.  "
                    "The file must be UTF-8 encoded and contain valid XML."
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
        file_path: str = kwargs.get("file_path", "")
        if not file_path:
            raise ParseError("<missing>", "Parameter 'file_path' is required")

        file_path = os.path.abspath(file_path)

        directed_raw: str = str(kwargs.get("directed", "true")).strip().lower()
        directed: bool = directed_raw not in ("false", "0", "no")

        parser = XMLParser(directed=directed)
        graph = parser.parse_file(file_path, directed=directed)
        return graph

    def __repr__(self) -> str:
        return "XMLDataSourcePlugin()"
