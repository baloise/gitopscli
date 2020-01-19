import argparse
import sys
import uuid
import shutil
import json
from atlassian import Bitbucket
from pprint import pprint
from .git_util import GitUtil
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


# Example
"""
gitopscli deploy --repo https://bitbucket.baloise.dev/scm/dpl/incubator-non-prod.git \
--file example/values.yaml \
--branch deploy-$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 5 | head -n 1) \
--values "{image.tag: v0.3.0}" \
--username $GIT_USERNAME \
--password $GIT_PASSWORD \
--create-pr \
--auto-merge \
--organisation "DPL" \
--repository-name "incubator-non-prod" \
--git-provider-url https://bitbucket.baloise.dev
"""


def add_deploy_parser(subparsers):
    deploy_p = subparsers.add_parser("deploy", help="Trigger a new deployment by changing YAML values")
    deploy_p.add_argument("-r", "--repo", help="Git repository URL", required=True)
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
        help="Creates a Pull Request (only when --branch is not master/default branch",
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
    repo,
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

    git = GitUtil(repo, branch, tmp_dir, username, password)

    full_file_path = git.get_full_file_path(file)

    for key in values:
        value = values[key]
        update_yaml_file(full_file_path, key, value)
        git.commit(f"changed '{key}' to '{value}'")

    git.push()
    shutil.rmtree(tmp_dir, ignore_errors=True)
    if create_pr and branch is not "master":
        if git_provider == "bitbucket-server":
            title = f"Updated values in {file}"
            description = f"""
This Pull Request is automatically created through gitopscli. 
Files changed: {file}
Values changed:
{json.dumps(values)}
"""
            pull_request = create_pr(
                branch,
                "master",
                organisation,
                repository_name,
                git_provider_url,
                username,
                password,
                title,
                description,
            )
            if auto_merge:
                merge_pr(
                    pull_request["id"],
                    pull_request["version"],
                    organisation,
                    repository_name,
                    git_provider_url,
                    username,
                    password,
                )
        else:
            print(f"Git provider {git_provider} is not supported.")
            exit(1)


def create_pr(
    from_branch, to_branch, organisation, repository_name, git_provider_url, username, password, title, description
):
    bitbucket = create_bitbucket_client(git_provider_url, username, password)
    pull_request = bitbucket.open_pull_request(
        organisation, repository_name, organisation, repository_name, from_branch, to_branch, title, description
    )

    # pprint(pull_request)
    if "errors" in pull_request:
        for e in pull_request["errors"]:
            print(e["message"])
        exit(1)
    pull_request_url = pull_request["links"]["self"][0]["href"]
    print(f"Pull request created: {pull_request_url}")
    return pull_request


def merge_pr(pr_id, pr_version, organisation, repository_name, git_provider_url, username, password):
    bitbucket = create_bitbucket_client(git_provider_url, username, password)
    merged = bitbucket.merge_pull_request(organisation, repository_name, pr_id, pr_version)
    print("Pull request merged")
    # pprint(merged)
    return merged


def create_bitbucket_client(git_provider_url, username, password):
    return Bitbucket(git_provider_url, username, password)


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


if __name__ == "__main__":
    main()
