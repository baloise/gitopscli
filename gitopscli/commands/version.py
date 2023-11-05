import importlib.metadata
from dataclasses import dataclass

from .command import Command


class VersionCommand(Command):
    @dataclass(frozen=True)
    class Args:
        pass

    def __init__(self, args: Args) -> None:
        pass

    def execute(self) -> None:
        try:
            version = importlib.metadata.version("gitopscli")
        except importlib.metadata.PackageNotFoundError:
            # Handle the case where "gitopscli" is not installed
            version = None
        print(f"GitOps CLI version {version}")
