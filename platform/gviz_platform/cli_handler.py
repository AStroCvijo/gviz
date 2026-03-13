import shlex

from gviz_platform.commands import *


class CLIHandler:
    def parse(self, command: str) -> Command:
        tokens = shlex.split(command, comments=False, posix=True)
        prefix = tokens[0].lower()
        parameters = [t for t in tokens[1:] if t != "" and t[0] != "-"]
        flags = [t for t in tokens[1:] if len(t) > 1 and t[0] == "-"]

        for command_type in Command.__subclasses__():
            if command_type.get_prefix() == prefix:
                return command_type(parameters, flags)

        raise CommandError(prefix, "Unknown command")