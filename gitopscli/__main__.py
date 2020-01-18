import argparse
import string
import sys
import uuid
import shutil
import requests
from pprint import pprint
from .git_util import GitUtil
from .yaml_util import yaml_load, update_yaml_file


def main():
    parser, subparsers = create_cli_parser()
    add_deploy_parser(subparsers)
    add_create_pr_parser(subparsers)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "deploy":
        deploy(args.repo, args.file, args.values, args.branch, args.username, args.password)

    if args.command == "create-pr":
        create_pr(args.from_branch, args.to_branch, args.organisation, args.repository_name, args.git_provider,
                  args.git_provider_url, args.username, args.password)


def create_cli_parser():
    parser = argparse.ArgumentParser(description="GitOps CLI")
    subparsers = parser.add_subparsers(title="commands")
    return parser, subparsers


def add_deploy_parser(subparsers):
    deploy_p = subparsers.add_parser("deploy", help="Trigger a new deployment by changing YAML values")
    deploy_p.set_defaults(command="deploy")
    deploy_p.add_argument("-r", "--repo", help="the repository URL", required=True)
    deploy_p.add_argument("-f", "--file", help="the YAML file path", required=True)
    deploy_p.add_argument(
        "-v", "--values", help="YAML string with key-value pairs to write", type=yaml_load, required=True,
    )
    deploy_p.add_argument("-b", "--branch", help="the branch to push the changes to", default="master")
    deploy_p.add_argument("-u", "--username", help="Git username if Basic Auth should be used")
    deploy_p.add_argument("-p", "--password", help="Git password if Basic Auth should be used")


def add_create_pr_parser(subparsers):
    create_pr_p = subparsers.add_parser("create-pr", help="Create a Pull Request")
    create_pr_p.set_defaults(command="create-pr")
    create_pr_p.add_argument("-f", "--from-branch", help="Create PR from branch (e.g. feature-branch-1)", required=True)
    create_pr_p.add_argument("-t", "--to-branch", help="Create PR to branch", required=True, default="master")
    create_pr_p.add_argument("-o", "--organisation", help="Git organisation/projectKey", required=True)
    create_pr_p.add_argument("-n", "--repository-name", help="Git repository name (not the URL, e.g. my-repo)",
                             required=True)
    create_pr_p.add_argument("-s", "--git-provider", help="Git server provider", default="bitbucket-server")
    create_pr_p.add_argument("-a", "--git-provider-url",
                             help="Git provider base API URL (e.g. https://bitbucket.example.tld)")
    create_pr_p.add_argument("-u", "--username", help="Username to authenticate against the git server", required=True)
    create_pr_p.add_argument("-p", "--password", help="Password to authenticate against the git server", required=True)


def deploy(repo, file_path, values, branch_name, username, password):
    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"

    git = GitUtil(repo, branch_name, tmp_dir, username, password)

    full_file_path = git.get_full_file_path(file_path)

    for key in values:
        value = values[key]
        update_yaml_file(full_file_path, key, value)
        git.commit(f"changed '{key}' to '{value}'")

    git.push()
    shutil.rmtree(tmp_dir, ignore_errors=True)


def create_pr(from_branch, to_branch, organisation, repository_name, git_provider, git_provider_url, username,
              password):
    # https://community.atlassian.com/t5/Bitbucket-questions/Creating-a-pull-request-via-API/qaq-p/123913
    # /rest/api/1.0/projects/{projectKey}/repos/{repositorySlug}/pull-requests
    request_url = f"{git_provider_url}/rest/api/1.0/projects/{organisation}/repos/{repository_name}/pull-requests"
    request_tpl = '''
{
    "title": "Request from CLI",
    "description": "First PR in Bitbucket via CLI",
    "state": "OPEN",
    "open": true,
    "closed": false,
    "fromRef": {
        "id": "refs/heads/${from_branch}",
        "repository": {
            "slug": "${repository_name}",
            "name": null,
            "project": {
                "key": "${organisation}"
            }
        }
    },
    "toRef": {
        "id": "refs/heads/${to_branch}",
        "repository": {
            "slug": "${repository_name}",
            "name": null,
            "project": {
                "key": "${organisation}"
            }
        }
    },
    "locked": false
}
'''
    request = string.Template(request_tpl).substitute(locals())
    headers = {'Content-type': 'application/json'}
    r = requests.post(request_url, data=request, auth=(username, password), headers=headers)
    if r.status_code is not 201:
        print("Status Code is " + str(r.status_code))
        pprint(vars(r))
        exit(1)


if __name__ == "__main__":
    main()
