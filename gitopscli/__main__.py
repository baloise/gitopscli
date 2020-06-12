import logging
import sys

from gitopscli.cliparser import create_cli
from gitopscli.commands import (
    pr_comment_command,
    create_preview_common_command,
    create_pr_preview_command,
    create_preview_command,
    delete_preview_command,
    deploy_command,
    sync_apps_command,
    version_command,
)
from gitopscli.gitops_exception import GitOpsException


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)-2s %(funcName)s: %(message)s")
    args = create_cli(sys.argv[1:])

    if args.command == "deploy":
        command = deploy_command
    elif args.command == "sync-apps":
        command = sync_apps_command
    elif args.command == "add-pr-comment":
        command = pr_comment_command
    elif args.command == "create-preview-common":
        command = create_preview_common_command
    elif args.command == "create-pr-preview":
        command = create_pr_preview_command
    elif args.command == "create-preview":
        command = create_preview_command
    elif args.command == "delete-preview":
        command = delete_preview_command
    elif args.command == "version":
        command = version_command

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
