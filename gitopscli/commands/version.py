from dataclasses import dataclass
import pkg_resources
from .command import Command


class VersionCommand(Command):
    @dataclass(frozen=True)
    class Args:
        pass

    def __init__(self, args: Args) -> None:
        pass

    def execute(self) -> None:
        version = pkg_resources.require("gitopscli")[0].version
        print(f"GitOps CLI version {version}")
