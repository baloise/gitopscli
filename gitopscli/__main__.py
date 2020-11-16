import logging
import sys
from typing import Callable

from gitopscli.cliparser import create_cli
from gitopscli.commands import (
    pr_comment_command,
    create_pr_preview_command,
    create_preview_command,
    delete_preview_command,
    deploy_command,
    sync_apps_command,
    version_command,
    delete_pr_preview_command,
)
from gitopscli.gitops_exception import GitOpsException


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-2s %(funcName)s: %(message)s")
    args = create_cli(sys.argv[1:])

    command = get_command(args.command)

    if "verbose" in args:
        verbose = args.verbose
        del args.verbose
    else:
        verbose = False

    try:
        command(**vars(args))
    except GitOpsException as ex:
        if verbose:
            logging.exception(ex)
        else:
            logging.error(ex)
        sys.exit(1)


if __name__ == "__main__":
    main()


def get_command(command: str) -> Callable[..., None]:
    command_func: Callable[..., None]
    if command == "deploy":
        command_func = deploy_command
    elif command == "sync-apps":
        command_func = sync_apps_command
    elif command == "add-pr-comment":
        command_func = pr_comment_command
    elif command == "create-pr-preview":
        command_func = create_pr_preview_command
    elif command == "create-preview":
        command_func = create_preview_command
    elif command == "delete-pr-preview":
        command_func = delete_pr_preview_command
    elif command == "delete-preview":
        command_func = delete_preview_command
    elif command == "version":
        command_func = version_command
    else:
        raise GitOpsException(f"Command {command} not implemented!")
    return command_func
