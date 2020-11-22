import pkg_resources


def version_command() -> None:
    version = pkg_resources.require("gitopscli")[0].version
    print(f"GitOps CLI version {version}")
