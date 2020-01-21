import argparse
import sys
import uuid
import shutil
import json
import os
from .bitbucket_git_util import BitBucketGitUtil
from .github_git_util import GithubGitUtil
from .yaml_util import yaml_load, update_yaml_file


def main():
    parser, subparsers = create_cli_parser()
    add_deploy_parser(subparsers)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "deploy":
        deploy(**vars(args))


def create_cli_parser():
    parser = argparse.ArgumentParser(description="GitOps CLI")
    subparsers = parser.add_subparsers(title="commands", dest="command")
    return parser, subparsers


def add_deploy_parser(subparsers):
    deploy_p = subparsers.add_parser("deploy", help="Trigger a new deployment by changing YAML values")
    deploy_p.add_argument("-f", "--file", help="YAML file path", required=True)
    deploy_p.add_argument(
        "-v",
        "--values",
        help="YAML/JSON object with the YAML path as key and the desired value as value",
        type=yaml_load,
        required=True,
    )
    deploy_p.add_argument("-b", "--branch", help="Branch to push the changes to", default="master")
    deploy_p.add_argument("-u", "--username", help="Git username if Basic Auth should be used")
    deploy_p.add_argument("-p", "--password", help="Git password if Basic Auth should be used")
    deploy_p.add_argument(
        "-c",
        "--create-pr",
        help="Creates a Pull Request (only when --branch is not master/default branch)",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
    )
    deploy_p.add_argument(
        "-a",
        "--auto-merge",
        help="Automatically merge the created PR (only valid with --create-pr)",
        type=str2bool,
        nargs="?",
        const=True,
        default=False,
    )
    deploy_p.add_argument("-o", "--organisation", help="Git organisation/projectKey", required=True)
    deploy_p.add_argument(
        "-n", "--repository-name", help="Git repository name (not the URL, e.g. my-repo)", required=True
    )
    deploy_p.add_argument("-s", "--git-provider", help="Git server provider", default="bitbucket-server")
    deploy_p.add_argument(
        "-w", "--git-provider-url", help="Git provider base API URL (e.g. https://bitbucket.example.tld)"
    )


def deploy(
    command,
    file,
    values,
    branch,
    username,
    password,
    create_pr,
    auto_merge,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
):
    assert command == "deploy"

    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(tmp_dir)

    try:
        if git_provider == "bitbucket-server":
            if not git_provider_url:
                print(f"Please provide --git-provider-url for bitbucket-server", file=sys.stderr)
                sys.exit(1)
            git = BitBucketGitUtil(tmp_dir, git_provider_url, organisation, repository_name, username, password)
        elif git_provider == "github":
            git = GithubGitUtil(tmp_dir, organisation, repository_name, username, password)
        else:
            print(f"Git provider '{git_provider}' is not supported.", file=sys.stderr)
            sys.exit(1)

        git.checkout(branch)

        full_file_path = git.get_full_file_path(file)
        for key in values:
            value = values[key]
            update_yaml_file(full_file_path, key, value)
            git.commit(f"changed '{key}' to '{value}'")

        git.push(branch)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    if create_pr and branch != "master":
        title = f"Updated values in {file}"
        description = f"""
This Pull Request is automatically created through [gitopscli](https://github.com/baloise-incubator/gitopscli).
Files changed: `{file}`
Values changed:
```json
{json.dumps(values)}
```
"""
        pull_request = git.create_pull_request(branch, "master", title, description)
        print(f"Pull request created: {git.get_pull_request_url(pull_request)}")

        if auto_merge:
            git.merge_pull_request(pull_request)
            print("Pull request merged")

            git.delete_branch(branch)
            print(f"Branch '{branch}' deleted")


def str2bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ("yes", "true", "t", "y", "1"):
        return True
    if value.lower() in ("no", "false", "f", "n", "0"):
        return False
    raise argparse.ArgumentTypeError("Boolean value expected.")


if __name__ == "__main__":
    main()
