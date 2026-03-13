import io
from abc import ABC, abstractmethod
from typing import List
import shlex

from api.exceptions import CommandError
from gviz_platform import Workspace, FilterEngine, ConcreteNode, ConcreteEdge, ConcreteGraph


class Command(ABC):
    def __init__(self, params: List[str], flags: List[str], rerender: bool):
        self.params = params
        self.flags = flags
        self.rerender = rerender

    @abstractmethod
    def execute(self, workspace: Workspace):
        """Executes the command"""

    @staticmethod
    @abstractmethod
    def get_prefix() -> str:
        """Returns identifier prefix to distinguish the command type"""

    @staticmethod
    @abstractmethod
    def get_help() -> str:
        """Returns the command help text"""


class FilterCommand(Command):
    def __init__(self, params: List[str], flags: List[str]):
        super().__init__(params, flags, False)
        self.supported_operations = ["==", ">", ">=", "<", "<=", "!="]

    def execute(self, workspace: Workspace):
        graph_before = workspace.current_graph
        if "--reset" in self.flags or "-r" in self.flags:
            workspace.reset()

        if len(self.params) < 1:
            self.rerender = workspace.current_graph != graph_before
            return f"Filter: {workspace.current_graph.node_count()} nodes found"

        i = 1
        filter_engine = FilterEngine()
        while True:
            if i * 3 + (i-1) > len(self.params):
                raise CommandError(FilterCommand.get_prefix(), "Invalid parameter count for last filter")

            filter_start = (i-1)*3 + (i-1)
            if self.params[filter_start + 1] not in self.supported_operations:
                raise CommandError(FilterCommand.get_prefix(), f"Invalid operation '{self.params[(i-1)*3 + 1]}'")

            if self.params[filter_start + 2] == "" or self.params[filter_start] == "":
                raise CommandError(FilterCommand.get_prefix(), f"Invalid operators in filter number {i}")

            expression = " ".join(self.params[filter_start: filter_start + 3])
            result = filter_engine.filter(workspace.current_graph, expression)
            workspace.apply_filter(expression, result)

            if len(self.params) == filter_start + 3:
                break

            if len(self.params) >= filter_start + 4 and self.params[filter_start + 3] != "&":
                raise CommandError(FilterCommand.get_prefix(), "Expected '&' delimiter before next filter")

            i+=1

        self.rerender = workspace.current_graph != graph_before
        return f"Filter: {workspace.current_graph.node_count()} nodes found"

    @staticmethod
    def get_prefix() -> str:
        return "filter"

    @staticmethod
    def get_help() -> str:
        return "filter [--reset | -r] [<property> <operator> <value> [& <property> <operator> <value>]...]"

class SearchCommand(Command):
    def __init__(self, params: List[str], flags: List[str]):
        super().__init__(params, flags, False)


    def execute(self, workspace: Workspace):
        graph_before = workspace.current_graph
        if "--reset" in self.flags or "-r" in self.flags:
            workspace.reset()

        if len(self.params) > 0:
            filter_engine = FilterEngine()
            workspace.applied_operations = [o for o in workspace.applied_operations if o["type"] != "search"]
            workspace.current_graph = workspace.original_graph
            for operation in workspace.applied_operations:
                workspace.current_graph = filter_engine.filter(workspace.current_graph, operation["query"])
            workspace.apply_search(self.params[0], filter_engine.search(workspace.current_graph, self.params[0]))

        self.rerender = workspace.current_graph != graph_before
        return f"Search: {workspace.current_graph.node_count()} nodes found"


    @staticmethod
    def get_prefix() -> str:
        return "search"

    @staticmethod
    def get_help() -> str:
        return "search [--reset | -r] [<query>]"

class CreateCommand(Command):
    def __init__(self, params: List[str], flags: List[str]):
        super().__init__(params, flags, False)


    def execute(self, workspace: Workspace):
        if len(self.params) < 1:
            raise CommandError(CreateCommand.get_prefix(), "Invalid parameter count")

        graph_before = workspace.current_graph
        filter_engine = FilterEngine()
        match self.params[0].lower():
            case "node":
                node_id = f"n{workspace.original_graph.node_count() + 1}"
                attr_dict = {}
                for param in self.params[1:]:
                    attr, value = self._parse_attribute(param)
                    if attr in ["id", "node_id"]:
                        node_id = value
                    else:
                        attr_dict[attr] = value

                node = ConcreteNode(node_id, attr_dict)
                try:
                    workspace.original_graph.add_node(node)
                    workspace.current_graph = workspace.original_graph
                    for operation in workspace.applied_operations:
                        if operation["type"] == "filter":
                            workspace.current_graph = filter_engine.filter(workspace.current_graph, operation["query"])
                        elif operation["type"] == "search":
                            workspace.current_graph = filter_engine.search(workspace.current_graph, operation["query"])
                    self.rerender = workspace.current_graph != graph_before
                except ValueError:
                    raise CommandError(CreateCommand.get_prefix(), "Invalid parameter count")

                return f"Create: Node with id '{node.get_id()}' has been created"
            case "edge":
                edge_id = f"e{workspace.original_graph.edge_count() + 1}"
                source_id = None
                target_id = None
                attr_dict = {}
                for param in self.params[1:]:
                    attr, value = self._parse_attribute(param)
                    if attr in ["id", "node_id"]:
                        edge_id = value
                    elif attr in ["source", "source_id"]:
                        source_id = value
                    elif attr in ["target", "target_id"]:
                        target_id = value
                    else:
                        attr_dict[attr] = value

                if source_id is None:
                    raise CommandError(CreateCommand.get_prefix(), "Missing edge source node")

                if target_id is None:
                    raise CommandError(CreateCommand.get_prefix(), "Missing edge target node")

                directed = "--directed" in self.flags or "-d" in self.flags
                edge = ConcreteEdge(edge_id, source_id, target_id, directed, attr_dict)
                try:
                    workspace.original_graph.add_edge(edge)
                except ValueError as err:
                    raise CommandError(CreateCommand.get_prefix(), str(err))
                try:
                    workspace.current_graph.add_edge(edge)
                    self.rerender = True
                except ValueError:
                    pass

                return f"Create: Edge with id '{edge.get_id()}' has been created"
            case _:
                raise CommandError(CreateCommand.get_prefix(), "First parameter must be object type")


    @staticmethod
    def get_prefix() -> str:
        return "create"

    @staticmethod
    def get_help() -> str:
        return """create node [<attr>=<value>]...\n    create edge [--directed | -d] source=<value> target=<value> [<attr>=<value>]..."""

    @staticmethod
    def _parse_attribute(attribute: str) -> (str, str):
        s = shlex.shlex(io.StringIO(attribute))
        s.whitespace = "="
        s.wordchars += "./\\-_#$^*!@)(+&` "
        tokens = list(s)
        tokens = [t for t in tokens if t]

        if len(tokens) != 2:
            raise CommandError(DeleteCommand.get_prefix(), f"Invalid attribute expression '{attribute}'")

        return tokens[0], tokens[1]

class EditCommand(Command):
    def __init__(self, params: List[str], flags: List[str]):
        super().__init__(params, flags, False)


    def execute(self, workspace: Workspace):
        if len(self.params) < 2:
            raise CommandError(EditCommand.get_prefix(), "Invalid parameter count")

        match self.params[0].lower():
            case "node":
                node_id = f"n{workspace.original_graph.node_count() + 1}"
                attr_dict = {}
                for param in self.params[1:]:
                    attr, value = self._parse_attribute(param)
                    if attr in ["id", "node_id"]:
                        node_id = value
                    else:
                        attr_dict[attr] = value

                old_node = workspace.original_graph.get_node_by_id(node_id)
                if old_node is None:
                    raise CommandError(EditCommand.get_prefix(), f"Unknown node id '{node_id}'")

                changed = False
                for new_attr, new_val in attr_dict.items():
                    if new_attr not in old_node.get_attributes() or new_val != old_node.get_attributes()[new_attr]:
                        changed = True
                    old_node.set_attribute(new_attr, new_val)

                node = ConcreteNode(node_id, old_node.get_attributes())
                workspace.original_graph.add_or_update_node(node)
                if workspace.current_graph.get_node_by_id(node_id) is not None:
                    workspace.current_graph.add_or_update_node(node)
                    self.rerender = changed

                return "Edit: Node successfully edited"
            case "edge":
                edge_id = f"e{workspace.original_graph.edge_count() + 1}"
                source_id = None
                target_id = None
                attr_dict = {}
                for param in self.params[1:]:
                    attr, value = self._parse_attribute(param)
                    if attr in ["id", "edge_id"]:
                        edge_id = value
                    elif attr in ["source", "source_id"]:
                        source_id = value
                    elif attr in ["target", "target_id"]:
                        target_id = value
                    else:
                        attr_dict[attr] = value

                old_edge = workspace.original_graph.get_edge_by_id(edge_id)
                if old_edge is None:
                    raise CommandError(EditCommand.get_prefix(), "Unknown edge id '{node_id}'")

                changed = False
                if source_id is None:
                    source_id = old_edge.get_source_id()
                elif source_id != old_edge.get_source_id():
                    changed = True

                if target_id is None:
                    target_id = old_edge.get_target_id()
                elif target_id != old_edge.get_target_id():
                    changed = True

                for new_attr, new_val in attr_dict.items():
                    if new_attr not in old_edge.get_attributes() or new_val != old_edge.get_attributes()[new_attr]:
                        changed = True
                    old_edge.set_attribute(new_attr, new_val)

                directed = "--directed" in self.flags or "-d" in self.flags
                edge = ConcreteEdge(edge_id, source_id, target_id, directed, old_edge.get_attributes())

                try:
                    workspace.original_graph.add_or_update_edge(edge)
                except ValueError as err:
                    raise CommandError(EditCommand.get_prefix(), str(err))
                try:
                    workspace.current_graph.add_or_update_edge(edge)
                    self.rerender = changed
                except ValueError:
                    pass

                return "Edit: Edge successfully edited"
            case _:
                raise CommandError(EditCommand.get_prefix(), "First parameter must be object type")


    @staticmethod
    def get_prefix() -> str:
        return "edit"

    @staticmethod
    def get_help() -> str:
        return """edit node id=<value> [<attr>=<value>]...\n    edit edge [--directed | -d] id=<value> [<attr>=<value>]..."""

    @staticmethod
    def _parse_attribute(attribute: str) -> (str, str):
        s = shlex.shlex(io.StringIO(attribute))
        s.whitespace = "="
        s.wordchars += "./\\-_#$^*!@)(+&` "
        tokens = list(s)
        tokens = [t for t in tokens if t]

        if len(tokens) != 2:
            raise CommandError(DeleteCommand.get_prefix(), f"Invalid attribute expression '{attribute}'")

        return tokens[0], tokens[1]

class DeleteCommand(Command):
    def __init__(self, params: List[str], flags: List[str]):
        super().__init__(params, flags, False)


    def execute(self, workspace: Workspace):
        if len(self.params) < 1 or (self.params[0] != "graph" and len(self.params) < 2):
            raise CommandError(DeleteCommand.get_prefix(), "Invalid parameter count")

        match self.params[0].lower():
            case "node":
                attr, value = DeleteCommand._parse_attribute(self.params[1])
                nodes = []
                for n in workspace.original_graph.get_nodes():
                    attributes = n.get_attributes()
                    is_attribute = (attributes != None and attr in attributes and str(attributes[attr]) == value)
                    is_id = (attr in ["id", "node_id"] and n.get_id() == value)
                    if is_attribute or is_id:
                        nodes.append(n)

                count = len(nodes)
                for node in nodes:
                    try:
                        workspace.original_graph.remove_node(node.get_id())
                        workspace.current_graph.remove_node(node.get_id())
                        self.rerender = True
                    except KeyError:
                        pass
                    except ValueError:
                        count-=1

                return f"Delete: {count}/{len(nodes)} selected nodes deleted"
            case "edge":
                attr, value = DeleteCommand._parse_attribute(self.params[1])
                edges = []
                for e in workspace.original_graph.get_edges():
                    attributes = e.get_attributes()
                    is_attribute = (attributes != None and attr in attributes and attributes[attr] == value)
                    is_id = (attr in ["id", "edge_id"] and e.get_id() == value)
                    is_source = (attr in ["source", "source_id"] and e.get_source_id() == value)
                    is_target = (attr in ["target", "target_id"] and e.get_target_id() == value)
                    if is_attribute or is_id or is_source or is_target:
                        edges.append(e)

                for edge in edges:
                    try:
                        workspace.original_graph.remove_edge(edge.get_id())
                        workspace.current_graph.remove_edge(edge.get_id())
                        self.rerender = True
                    except KeyError:
                        pass

                return f"Delete: {len(edges)} selected edges deleted"
            case "graph":
                new_graph = ConcreteGraph(workspace.original_graph.is_directed())
                workspace.original_graph = new_graph
                workspace.current_graph = new_graph

                self.rerender = True
                return "Delete: Graph cleared"
            case _:
                raise CommandError(DeleteCommand.get_prefix(), "First parameter must be object type")

    @staticmethod
    def get_prefix() -> str:
        return "delete"

    @staticmethod
    def get_help() -> str:
        return """delete node <attr>=<value>\n    delete edge <attr>=<value>\n    delete graph"""

    @staticmethod
    def _parse_attribute(attribute: str) -> (str, str):
        s = shlex.shlex(io.StringIO(attribute))
        s.whitespace = "="
        s.wordchars += "./\\-_#$^*!@)(+&` "
        tokens = list(s)
        tokens = [t for t in tokens if t]

        if len(tokens) != 2:
            raise CommandError(DeleteCommand.get_prefix(), f"Invalid attribute expression '{attribute}'")

        return tokens[0], tokens[1]

class HelpCommand(Command):
    def __init__(self, params: List[str], flags: List[str]):
        super().__init__(params, flags, False)


    def execute(self, workspace: Workspace):
        target_command = self.params[0] if len(self.params) > 0  else ""

        out = "  Command syntax:\n"
        for command_type in Command.__subclasses__():
            if target_command == "" or command_type.get_prefix() == target_command:
                out += "    " + command_type.get_help() + "\n"

        return out


    @staticmethod
    def get_prefix() -> str:
        return "help"

    @staticmethod
    def get_help() -> str:
        commands = ""
        for command_type in Command.__subclasses__():
            commands += command_type.get_prefix() + " | "

        return f"help [{commands[0:-3]}]"
