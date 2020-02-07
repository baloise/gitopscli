import argparse
import sys

from gitopscli.yaml.yaml_util import yaml_load


def create_cli():
    parser, subparsers = __create_cli_parser()
    __add_deploy_command_parser(subparsers)
    __add_sync_apps_command_parser(subparsers)
    __add_pr_comment_command_parser(subparsers)
    __add_create_preview_command_parser(subparsers)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    return parser.parse_args()


def __create_cli_parser():
    parser = argparse.ArgumentParser(description="GitOps CLI")
    subparsers = parser.add_subparsers(title="commands", dest="command")
    return parser, subparsers


def __add_deploy_command_parser(subparsers):
    deploy_p = subparsers.add_parser("deploy", help="Trigger a new deployment by changing YAML values")
    deploy_p.add_argument("-f", "--file", help="YAML file path", required=True)
    deploy_p.add_argument(
        "-v",
        "--values",
        help="YAML/JSON object with the YAML path as key and the desired value as value",
        type=yaml_load,
        required=True,
    )

    __add_git_parser_args(deploy_p)


def __add_sync_apps_command_parser(subparsers):
    sync_apps_p = subparsers.add_parser(
        "sync-apps", help="Synchronize applications (= every directory) from apps config repository to apps root config"
    )
    __add_git_parser_args(sync_apps_p)
    sync_apps_p.add_argument("-i", "--root-organisation", help="Apps config repository organisation", required=True)
    sync_apps_p.add_argument("-r", "--root-repository-name", help="Root config repository organisation", required=True)


def __add_pr_comment_command_parser(subparsers):
    add_pr_comment_p = subparsers.add_parser("add-pr-comment", help="Create a comment on the pull request")
    __add_git_parser_args(add_pr_comment_p)
    __add_create_prid_parser(add_pr_comment_p)
    add_pr_comment_p.add_argument("-t", "--text", help="the text of the comment", required=True)


def __add_create_preview_command_parser(subparsers):
    add_create_preview_p = subparsers.add_parser("create-preview", help="Create a preview environment")
    __add_git_parser_args(add_create_preview_p)
    __add_create_prid_parser(add_create_preview_p)


def __add_git_parser_args(deploy_p):
    deploy_p.add_argument("-b", "--branch", help="Branch to push the changes to", default="master")
    deploy_p.add_argument("-u", "--username", help="Git username if Basic Auth should be used")
    deploy_p.add_argument("-p", "--password", help="Git password if Basic Auth should be used")
    deploy_p.add_argument("-j", "--git-user", help="Git Username", default="GitOpsCLI")
    deploy_p.add_argument("-e", "--git-email", help="Git User Email", default="gitopscli@baloise.dev")
    deploy_p.add_argument(
        "-c",
        "--create-pr",
        help="Creates a Pull Request (only when --branch is not master/default branch)",
        type=__str2bool,
        nargs="?",
        const=True,
        default=False,
    )
    deploy_p.add_argument(
        "-a",
        "--auto-merge",
        help="Automatically merge the created PR (only valid with --create-pr)",
        type=__str2bool,
        nargs="?",
        const=True,
        default=False,
    )
    deploy_p.add_argument("-o", "--organisation", help="Apps Git organisation/projectKey", required=True)
    deploy_p.add_argument(
        "-n", "--repository-name", help="Git repository name (not the URL, e.g. my-repo)", required=True
    )
    deploy_p.add_argument("-s", "--git-provider", help="Git server provider", default="bitbucket-server")
    deploy_p.add_argument(
        "-w", "--git-provider-url", help="Git provider base API URL (e.g. https://bitbucket.example.tld)"
    )


def __add_create_prid_parser(subparsers):
    subparsers.add_argument("-i", "--pr-id", help="the id of the pull request", type=int, required=True)
    subparsers.add_argument("-x", "--parent-id", help="the id of the parent comment, in case of a reply", type=int)


def __str2bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if value.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")
