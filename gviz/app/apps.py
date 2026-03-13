#Django AppConfig for the gviz graph explorer application

from django.apps import AppConfig


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    # These attributes are set in ready() and shared across all requests.
    plugin_manager = None
    workspace_manager = None
    filter_engine = None

    def ready(self) -> None:
        """Initialise the platform services once Django has started"""
        try:
            from gviz_platform.plugin_manager import PluginManager
            from gviz_platform.workspace import WorkspaceManager
            from gviz_platform.filter_engine import FilterEngine
            from gviz_platform.cli_handler import CLIHandler

            AppConfig.plugin_manager = PluginManager()
            AppConfig.plugin_manager.discover()
            AppConfig.workspace_manager = WorkspaceManager()
            AppConfig.filter_engine = FilterEngine()
            AppConfig.cli_handler = CLIHandler()
        except ImportError:
            # Platform packages not yet installed — UI works with mock data.
            pass
