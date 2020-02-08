import logging
import sys

from gitopscli.cliparser import create_cli
from gitopscli.commands.add_pr_comment import pr_comment_command
from gitopscli.commands.create_preview import create_preview_command
from gitopscli.commands.deploy import deploy_command
from gitopscli.commands.sync_apps import sync_apps_command
from gitopscli.gitops_exception import GitOpsException


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')
    args = create_cli()

    if args.command == "deploy":
        command = deploy_command
    elif args.command == "sync-apps":
        command = sync_apps_command
    elif args.command == "add-pr-comment":
        command = pr_comment_command
    elif args.command == "create-preview":
        command = create_preview_command

    try:
        command(**vars(args))
    except GitOpsException as ex:
        logging.error(ex)
        sys.exit(1)


if __name__ == "__main__":
    main()
