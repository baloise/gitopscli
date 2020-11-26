from typing import NamedTuple
import pkg_resources
from .command import Command


class VersionCommand(Command):
    class Args(NamedTuple):
        pass

    def __init__(self, args: Args) -> None:
        pass

    def execute(self) -> None:
        version = pkg_resources.require("gitopscli")[0].version
        print(f"GitOps CLI version {version}")
