import logging

from gitopscli.cliparser import createCli
from gitopscli.commands.add_pr_comment import pr_comment_command
from gitopscli.commands.create_preview import create_preview_command
from gitopscli.commands.deploy import deploy
from gitopscli.commands.sync_apps import sync_apps_command


def main():
    logging.basicConfig(level=logging.INFO)

    args = createCli()

    if args.command == "deploy":
        deploy(**vars(args))

    if args.command == "sync-apps":
        sync_apps_command(**vars(args))

    if args.command == "add-pr-comment":
        pr_comment_command(**vars(args))

    if args.command == "create-preview":
        create_preview_command(**vars(args))


if __name__ == "__main__":
    main()
