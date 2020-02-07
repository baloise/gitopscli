import logging

from gitopscli.cliparser import create_cli
from gitopscli.commands.add_pr_comment import pr_comment_command
from gitopscli.commands.create_preview import create_preview_command
from gitopscli.commands.deploy import deploy_command
from gitopscli.commands.sync_apps import sync_apps_command


def main():
    logging.basicConfig(level=logging.INFO)

    args = create_cli()

    if args.command == "deploy":
        deploy_command(**vars(args))

    if args.command == "sync-apps":
        sync_apps_command(**vars(args))

    if args.command == "add-pr-comment":
        pr_comment_command(**vars(args))

    if args.command == "create-preview":
        create_preview_command(**vars(args))


if __name__ == "__main__":
    main()
