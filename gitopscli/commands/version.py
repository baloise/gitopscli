import pkg_resources


def version_command(command: str) -> None:
    assert command == "version"
    version = pkg_resources.require("gitopscli")[0].version
    print(f"GitOps CLI version {version}")
