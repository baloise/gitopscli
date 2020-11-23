from typing import NamedTuple
import pkg_resources


class VersionArgs(NamedTuple):
    pass


def version_command() -> None:
    version = pkg_resources.require("gitopscli")[0].version
    print(f"GitOps CLI version {version}")
