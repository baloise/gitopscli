from argparse import ArgumentParser, ArgumentTypeError, _SubParsersAction as SubParsersAction
import sys
from typing import List, Tuple
from gitopscli.commands import (
    CommandArgs,
    DeployCommand,
    SyncAppsCommand,
    AddPrCommentCommand,
    CreatePreviewCommand,
    CreatePrPreviewCommand,
    DeletePreviewCommand,
    DeletePrPreviewCommand,
    VersionCommand,
)
from gitopscli.io.yaml_util import yaml_load


def parse_args(raw_args: List[str]) -> Tuple[bool, CommandArgs]:
    parser, subparsers = __create_cli_parser()
    __add_deploy_command_parser(subparsers)
    __add_sync_apps_command_parser(subparsers)
    __add_pr_comment_command_parser(subparsers)
    __add_create_preview_command_parser(subparsers)
    __add_create_pr_preview_command_parser(subparsers)
    __add_delete_preview_command_parser(subparsers)
    __add_delete_pr_preview_command_parser(subparsers)
    __add_version_command_parser(subparsers)

    if len(raw_args) == 0:
        parser.print_help(sys.stderr)
        sys.exit(2)

    parsed_args = parser.parse_args(raw_args)

    verbose = False
    if "verbose" in parsed_args:
        verbose = parsed_args.verbose
        del parsed_args.verbose

    command = parsed_args.command
    del parsed_args.command

    typed_args: CommandArgs

    if command == "deploy":
        typed_args = DeployCommand.Args(**vars(parsed_args))
    elif command == "sync-apps":
        typed_args = SyncAppsCommand.Args(**vars(parsed_args))
    elif command == "add-pr-comment":
        typed_args = AddPrCommentCommand.Args(**vars(parsed_args))
    elif command == "create-preview":
        typed_args = CreatePreviewCommand.Args(**vars(parsed_args))
    elif command == "create-pr-preview":
        typed_args = CreatePrPreviewCommand.Args(**vars(parsed_args))
    elif command == "delete-preview":
        typed_args = DeletePreviewCommand.Args(**vars(parsed_args))
    elif command == "delete-pr-preview":
        typed_args = DeletePrPreviewCommand.Args(**vars(parsed_args))
    elif command == "version":
        typed_args = VersionCommand.Args()
    else:
        raise NotImplementedError(f"Unknown command: {command}")

    return verbose, typed_args


def __create_cli_parser() -> Tuple[ArgumentParser, SubParsersAction]:
    parser = ArgumentParser(prog="gitopscli", description="GitOps CLI")
    subparsers = parser.add_subparsers(title="commands", dest="command")
    return parser, subparsers


def __add_deploy_command_parser(subparsers: SubParsersAction) -> None:
    deploy_p = subparsers.add_parser("deploy", help="Trigger a new deployment by changing YAML values")
    deploy_p.add_argument("--file", help="YAML file path", required=True)
    deploy_p.add_argument(
        "--values",
        help="YAML/JSON object with the YAML path as key and the desired value as value",
        type=yaml_load,
        required=True,
    )
    deploy_p.add_argument(
        "--single-commit",
        help="Create only single commit for all updates",
        type=__parse_bool,
        nargs="?",
        const=True,
        default=False,
    )
    deploy_p.add_argument(
        "--commit-message", help="Specify exact commit message of deployment commit", type=str, default=None,
    )

    __add_git_parser_args(deploy_p)
    __add_branch_pr_parser_args(deploy_p)
    __add_verbose_parser(deploy_p)


def __add_sync_apps_command_parser(subparsers: SubParsersAction) -> None:
    sync_apps_p = subparsers.add_parser(
        "sync-apps", help="Synchronize applications (= every directory) from apps config repository to apps root config"
    )
    __add_git_parser_args(sync_apps_p)
    __add_verbose_parser(sync_apps_p)
    sync_apps_p.add_argument("--root-organisation", help="Root config repository organisation", required=True)
    sync_apps_p.add_argument("--root-repository-name", help="Root config repository name", required=True)


def __add_pr_comment_command_parser(subparsers: SubParsersAction) -> None:
    add_pr_comment_p = subparsers.add_parser("add-pr-comment", help="Create a comment on the pull request")
    __add_git_parser_args(add_pr_comment_p, api_only=True)
    __add_create_prid_parser(add_pr_comment_p)
    __add_verbose_parser(add_pr_comment_p)
    add_pr_comment_p.add_argument("--text", help="the text of the comment", required=True)


def __add_create_preview_command_parser(subparsers: SubParsersAction) -> None:
    add_create_preview_common_p = subparsers.add_parser("create-preview", help="Create a preview environment")
    __add_git_parser_args(add_create_preview_common_p)
    __add_create_githash_previewid_parser(add_create_preview_common_p)
    __add_verbose_parser(add_create_preview_common_p)


def __add_create_pr_preview_command_parser(subparsers: SubParsersAction) -> None:
    add_create_pr_preview_p = subparsers.add_parser("create-pr-preview", help="Create a preview environment")
    __add_git_parser_args(add_create_pr_preview_p)
    __add_create_prid_parser(add_create_pr_preview_p)
    __add_verbose_parser(add_create_pr_preview_p)


def __add_delete_preview_command_parser(subparsers: SubParsersAction) -> None:
    add_delete_preview_p = subparsers.add_parser("delete-preview", help="Delete a preview environment")
    __add_git_parser_args(add_delete_preview_p)
    add_delete_preview_p.add_argument(
        "--preview-id", help="The preview-id for which the preview was created for", required=True
    )
    __add_expect_preview_exists_parser(add_delete_preview_p)
    __add_verbose_parser(add_delete_preview_p)


def __add_delete_pr_preview_command_parser(subparsers: SubParsersAction) -> None:
    add_delete_preview_p = subparsers.add_parser("delete-pr-preview", help="Delete a pr preview environment")
    __add_git_parser_args(add_delete_preview_p)
    add_delete_preview_p.add_argument(
        "--branch", help="The branch for which the preview was created for", required=True
    )
    __add_expect_preview_exists_parser(add_delete_preview_p)
    __add_verbose_parser(add_delete_preview_p)


def __add_version_command_parser(subparsers: SubParsersAction) -> None:
    subparsers.add_parser("version", help="Show the GitOps CLI version information")


def __add_git_parser_args(deploy_p: ArgumentParser, api_only: bool = False) -> None:
    deploy_p.add_argument("--username", help="Git username", required=True)
    deploy_p.add_argument("--password", help="Git password or token", required=True)
    if not api_only:
        deploy_p.add_argument("--git-user", help="Git Username", default="GitOpsCLI")
        deploy_p.add_argument("--git-email", help="Git User Email", default="gitopscli@baloise.dev")
    deploy_p.add_argument("--organisation", help="Apps Git organisation/projectKey", required=True)
    deploy_p.add_argument("--repository-name", help="Git repository name (not the URL, e.g. my-repo)", required=True)
    deploy_p.add_argument("--git-provider", help="Git server provider")
    deploy_p.add_argument("--git-provider-url", help="Git provider base API URL (e.g. https://bitbucket.example.tld)")


def __add_branch_pr_parser_args(deploy_p: ArgumentParser) -> None:
    deploy_p.add_argument(
        "--create-pr", help="Creates a Pull Request", type=__parse_bool, nargs="?", const=True, default=False,
    )
    deploy_p.add_argument(
        "--auto-merge",
        help="Automatically merge the created PR (only valid with --create-pr)",
        type=__parse_bool,
        nargs="?",
        const=True,
        default=False,
    )


def __add_create_githash_previewid_parser(subparsers: ArgumentParser) -> None:
    subparsers.add_argument("--git-hash", help="the git hash which should be deployed", type=str, required=True)
    subparsers.add_argument(
        "--preview-id", help="the id of folder in the config repo which will be created", type=str, required=True
    )


def __add_create_prid_parser(subparsers: ArgumentParser) -> None:
    subparsers.add_argument("--pr-id", help="the id of the pull request", type=int, required=True)
    subparsers.add_argument("--parent-id", help="the id of the parent comment, in case of a reply", type=int)


def __add_expect_preview_exists_parser(subparsers: ArgumentParser) -> None:
    subparsers.add_argument(
        "--expect-preview-exists",
        help="Fail if preview does not exist",
        type=__parse_bool,
        nargs="?",
        const=True,
        default=False,
    )


def __add_verbose_parser(subparsers: ArgumentParser) -> None:
    subparsers.add_argument(
        "-v", "--verbose", help="Verbose exception logging", type=__parse_bool, nargs="?", const=True, default=False,
    )


def __parse_bool(value: str) -> bool:
    lowercase_value = value.lower()
    if lowercase_value in ("yes", "true", "t", "y", "1"):
        return True
    if lowercase_value in ("no", "false", "f", "n", "0"):
        return False
    raise ArgumentTypeError("Boolean value expected.")
