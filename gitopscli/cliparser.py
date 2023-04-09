from argparse import ArgumentParser, ArgumentTypeError
import os
import sys
from typing import List, Tuple, Dict, Any, NoReturn, Callable
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
from gitopscli.git_api import GitProvider
from gitopscli.io_api.yaml_util import yaml_load, YAMLException


def parse_args(raw_args: List[str]) -> Tuple[bool, CommandArgs]:
    parser = __create_parser()

    if len(raw_args) == 0:
        __print_help_and_exit(parser)

    args = vars(parser.parse_args(raw_args))
    args = __deduce_empty_git_provider_from_git_provider_url(args, parser.error)

    verbose = args.pop("verbose", False)
    command_args = __create_command_args(args)

    return verbose, command_args


def __create_parser() -> ArgumentParser:
    parser = ArgumentParser(prog="gitopscli", description="GitOps CLI")
    subparsers = parser.add_subparsers(title="commands", dest="command")
    subparsers.add_parser(
        "deploy", help="Trigger a new deployment by changing YAML values", parents=[__create_deploy_parser()]
    )
    subparsers.add_parser(
        "sync-apps",
        help="Synchronize applications (= every directory) from apps config repository to apps root config",
        parents=[__create_sync_apps_parser()],
    )
    subparsers.add_parser(
        "add-pr-comment", help="Create a comment on the pull request", parents=[__create_add_pr_comment_parser()]
    )
    subparsers.add_parser(
        "create-preview", help="Create a preview environment", parents=[__create_create_preview_parser()]
    )
    subparsers.add_parser(
        "create-pr-preview", help="Create a preview environment", parents=[__create_create_pr_preview_parser()]
    )
    subparsers.add_parser(
        "delete-preview", help="Delete a preview environment", parents=[__create_delete_preview_parser()]
    )
    subparsers.add_parser(
        "delete-pr-preview", help="Delete a pr preview environment", parents=[__create_delete_pr_preview_parser()]
    )
    subparsers.add_parser(
        "version", help="Show the GitOps CLI version information", parents=[__create_version_parser()]
    )
    return parser


def __create_deploy_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    parser.add_argument("--file", help="YAML file path", required=True)
    parser.add_argument(
        "--values",
        help="YAML/JSON object with the YAML path as key and the desired value as value",
        type=__parse_yaml,
        required=True,
    )
    parser.add_argument(
        "--single-commit",
        help="Create only single commit for all updates",
        type=__parse_bool,
        nargs="?",
        const=True,
        default=False,
    )
    parser.add_argument(
        "--commit-message", help="Specify exact commit message of deployment commit", type=str, default=None
    )
    __add_git_credentials_args(parser)
    __add_git_commit_user_args(parser)
    __add_git_org_and_repo_args(parser)
    __add_git_provider_args(parser)
    parser.add_argument(
        "--create-pr", help="Creates a Pull Request", type=__parse_bool, nargs="?", const=True, default=False
    )
    parser.add_argument(
        "--auto-merge",
        help="Automatically merge the created PR (only valid with --create-pr)",
        type=__parse_bool,
        nargs="?",
        const=True,
        default=False,
    )
    parser.add_argument(
        "--merge-method",
        help="Merge Method (e.g., 'squash', 'rebase', 'merge') (default: merge)",
        type=str,
        default="merge",
    )
    parser.add_argument(
        "--json",
        help="Print a JSON object containing deployment information",
        nargs="?",
        type=__parse_bool,
        default=False,
    )
    parser.add_argument(
        "--pr-labels", help="JSON array pr labels (Gitlab, Github supported)", type=__parse_yaml, default=None
    )
    parser.add_argument(
        "--merge-parameters",
        help="JSON object pr parameters (only Gitlab supported)",
        type=__parse_yaml,
        default=None,
    )
    __add_verbose_arg(parser)
    return parser


def __create_sync_apps_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    __add_git_credentials_args(parser)
    __add_git_commit_user_args(parser)
    __add_git_org_and_repo_args(parser)
    __add_git_provider_args(parser)
    __add_verbose_arg(parser)
    parser.add_argument("--root-organisation", help="Root config repository organisation", required=True)
    parser.add_argument("--root-repository-name", help="Root config repository name", required=True)
    return parser


def __create_add_pr_comment_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    __add_git_credentials_args(parser)
    __add_git_org_and_repo_args(parser)
    __add_git_provider_args(parser)
    __add_pr_id_arg(parser)
    __add_parent_id_arg(parser)
    __add_verbose_arg(parser)
    parser.add_argument("--text", help="the text of the comment", required=True)
    return parser


def __create_create_preview_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    __add_git_credentials_args(parser)
    __add_git_commit_user_args(parser)
    __add_git_org_and_repo_args(parser)
    __add_git_provider_args(parser)
    parser.add_argument("--git-hash", help="the git hash which should be deployed", type=str, required=True)
    __add_preview_id_arg(parser)
    __add_verbose_arg(parser)
    return parser


def __create_create_pr_preview_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    __add_git_credentials_args(parser)
    __add_git_commit_user_args(parser)
    __add_git_org_and_repo_args(parser)
    __add_git_provider_args(parser)
    __add_pr_id_arg(parser)
    __add_parent_id_arg(parser)
    __add_verbose_arg(parser)
    return parser


def __create_delete_preview_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    __add_git_credentials_args(parser)
    __add_git_commit_user_args(parser)
    __add_git_org_and_repo_args(parser)
    __add_git_provider_args(parser)
    __add_preview_id_arg(parser)
    __add_expect_preview_exists_arg(parser)
    __add_verbose_arg(parser)
    return parser


def __create_delete_pr_preview_parser() -> ArgumentParser:
    parser = ArgumentParser(add_help=False)
    __add_git_credentials_args(parser)
    __add_git_commit_user_args(parser)
    __add_git_org_and_repo_args(parser)
    __add_git_provider_args(parser)
    parser.add_argument("--branch", help="The branch for which the preview was created for", required=True)
    __add_expect_preview_exists_arg(parser)
    __add_verbose_arg(parser)
    return parser


def __create_version_parser() -> ArgumentParser:
    return ArgumentParser(add_help=False)


def __add_git_credentials_args(deploy_p: ArgumentParser) -> None:
    deploy_p.add_argument(
        "--username",
        help="Git username (alternative: GITOPSCLI_USERNAME env variable)",
        required="GITOPSCLI_USERNAME" not in os.environ,
        default=os.environ.get("GITOPSCLI_USERNAME"),
    )
    deploy_p.add_argument(
        "--password",
        help="Git password or token (alternative: GITOPSCLI_PASSWORD env variable)",
        required="GITOPSCLI_PASSWORD" not in os.environ,
        default=os.environ.get("GITOPSCLI_PASSWORD"),
    )


def __add_git_commit_user_args(deploy_p: ArgumentParser) -> None:
    deploy_p.add_argument("--git-user", help="Git Username", default="GitOpsCLI")
    deploy_p.add_argument("--git-email", help="Git User Email", default="gitopscli@baloise.dev")


def __add_git_org_and_repo_args(deploy_p: ArgumentParser) -> None:
    deploy_p.add_argument("--organisation", help="Apps Git organisation/projectKey", required=True)
    deploy_p.add_argument("--repository-name", help="Git repository name (not the URL, e.g. my-repo)", required=True)


def __add_git_provider_args(deploy_p: ArgumentParser) -> None:
    deploy_p.add_argument("--git-provider", help="Git server provider", type=__parse_git_provider)
    deploy_p.add_argument("--git-provider-url", help="Git provider base API URL (e.g. https://bitbucket.example.tld)")


def __add_pr_id_arg(parser: ArgumentParser) -> None:
    parser.add_argument("--pr-id", help="the id of the pull request", type=int, required=True)


def __add_parent_id_arg(parser: ArgumentParser) -> None:
    parser.add_argument("--parent-id", help="the id of the parent comment, in case of a reply", type=int)


def __add_preview_id_arg(parser: ArgumentParser) -> None:
    parser.add_argument("--preview-id", help="The user-defined preview ID", type=str, required=True)


def __add_expect_preview_exists_arg(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--expect-preview-exists",
        help="Fail if preview does not exist",
        type=__parse_bool,
        nargs="?",
        const=True,
        default=False,
    )


def __add_verbose_arg(parser: ArgumentParser) -> None:
    parser.add_argument(
        "-v", "--verbose", help="Verbose exception logging", type=__parse_bool, nargs="?", const=True, default=False
    )


def __parse_bool(value: str) -> bool:
    lowercase_value = value.lower()
    if lowercase_value in ("yes", "true", "t", "y", "1"):
        return True
    if lowercase_value in ("no", "false", "f", "n", "0"):
        return False
    raise ArgumentTypeError(f"invalid bool value: '{value}'")


def __parse_yaml(value: str) -> Any:
    try:
        return yaml_load(value)
    except YAMLException as ex:
        raise ArgumentTypeError(f"invalid YAML value: '{value}'") from ex


def __parse_git_provider(value: str) -> GitProvider:
    mapping = {"github": GitProvider.GITHUB, "bitbucket-server": GitProvider.BITBUCKET, "gitlab": GitProvider.GITLAB}
    assert set(mapping.values()) == set(GitProvider), "git provider mapping not exhaustive"
    lowercase_stripped_value = value.lower().strip()
    if lowercase_stripped_value not in mapping:
        raise ArgumentTypeError(f"invalid git provider value: '{value}'")
    return mapping[lowercase_stripped_value]


def __print_help_and_exit(parser: ArgumentParser) -> NoReturn:
    parser.print_help(sys.stderr)
    parser.exit(2)


def __deduce_empty_git_provider_from_git_provider_url(
    args: Dict[str, Any], error: Callable[[str], NoReturn]
) -> Dict[str, Any]:
    if "git_provider" not in args or args["git_provider"] is not None:
        return args
    git_provider_url = args["git_provider_url"]
    updated_args = dict(args)
    if git_provider_url is None:
        error("please provide either --git-provider or --git-provider-url")
    elif "github" in git_provider_url.lower():
        updated_args["git_provider"] = GitProvider.GITHUB
    elif "bitbucket" in git_provider_url.lower():
        updated_args["git_provider"] = GitProvider.BITBUCKET
    elif "gitlab" in git_provider_url.lower():
        updated_args["git_provider"] = GitProvider.GITLAB
    else:
        error("Cannot deduce git provider from --git-provider-url. Please provide --git-provider")
    return updated_args


def __create_command_args(args: Dict[str, Any]) -> CommandArgs:
    args = dict(args)
    command = args.pop("command")

    command_args: CommandArgs
    if command == "deploy":
        command_args = DeployCommand.Args(**args)
    elif command == "sync-apps":
        command_args = SyncAppsCommand.Args(**args)
    elif command == "add-pr-comment":
        command_args = AddPrCommentCommand.Args(**args)
    elif command == "create-preview":
        command_args = CreatePreviewCommand.Args(**args)
    elif command == "create-pr-preview":
        command_args = CreatePrPreviewCommand.Args(**args)
    elif command == "delete-preview":
        command_args = DeletePreviewCommand.Args(**args)
    elif command == "delete-pr-preview":
        command_args = DeletePrPreviewCommand.Args(**args)
    elif command == "version":
        command_args = VersionCommand.Args()
    else:
        raise RuntimeError(f"Unknown command: {command}")
    return command_args
