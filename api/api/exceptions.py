# Exceptions

class GvizError(Exception):
    """Base exception for all gviz errors."""


class PluginError(GvizError):
    # Raised when a plugin fails to initialise or execute correctly.

    def __init__(self, plugin_name: str, message: str) -> None:
        self.plugin_name = plugin_name
        super().__init__(f"[{plugin_name}] {message}")


class ParseError(GvizError):
    # Raised when the input data cannot be parsed or the resulting graph cannot be constructed.

    def __init__(self, source: str, message: str) -> None:
        self.source = source
        super().__init__(f"Failed to parse '{source}': {message}")


class FilterError(GvizError):
    #Raised by the platform's filter engine when a filter expression cannot be parsed or evaluated.

    def __init__(self, expression: str, message: str) -> None:
        self.expression = expression
        super().__init__(f"Invalid filter '{expression}': {message}")


class WorkspaceError(GvizError):
    # Raised when a workspace operation cannot be completed.

    def __init__(self, workspace_id: str, message: str) -> None:
        self.workspace_id = workspace_id
        super().__init__(f"Workspace '{workspace_id}': {message}")

class CommandError(GvizError):
    #Raised by platforms cli handler when syntax of a command is incorrect.

    def __init__(self, command: str, message: str) -> None:
        self.command = command
        super().__init__(f"Invalid command '{command}': {message}")
