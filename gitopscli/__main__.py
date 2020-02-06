import argparse
import json
import os
import shutil
import sys
import uuid
import logging
import hashlib

from gitopscli.apps_sync import sync_apps
from gitopscli.gitops_config import GitOpsConfig
from .create_git import create_git
from .yaml_util import yaml_load, update_yaml_file


def sync_apps_command(args):
    assert args.command == "sync-apps"

    apps_tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(apps_tmp_dir)
    root_tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(root_tmp_dir)

    try:
        apps_git = create_git(
            args.username,
            args.password,
            args.git_user,
            args.git_email,
            args.organisation,
            args.repository_name,
            args.git_provider,
            args.git_provider_url,
            apps_tmp_dir,
        )
        root_git = create_git(
            args.username,
            args.password,
            args.git_user,
            args.git_email,
            args.root_organisation,
            args.root_repository_name,
            args.git_provider,
            args.git_provider_url,
            root_tmp_dir,
        )

        sync_apps(apps_git, root_git)
    finally:
        shutil.rmtree(apps_tmp_dir, ignore_errors=True)
        shutil.rmtree(root_tmp_dir, ignore_errors=True)


def pr_comment_command(args):
    assert args.command == "add-pr-comment"
    apps_tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(apps_tmp_dir)
    try:
        apps_git = create_git(
            args.username,
            args.password,
            args.git_user,
            args.git_email,
            args.organisation,
            args.repository_name,
            args.git_provider,
            args.git_provider_url,
            apps_tmp_dir,
        )

        apps_git.add_pull_request_comment(args.pr_id, args.text, args.parent_id)

    finally:
        shutil.rmtree(apps_tmp_dir, ignore_errors=True)


def create_preview_command(args):
    assert args.command == "create-preview"

    apps_tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(apps_tmp_dir)
    root_tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(root_tmp_dir)

    try:
        apps_git = create_git(
            args.username,
            args.password,
            args.git_user,
            args.git_email,
            args.organisation,
            args.repository_name,
            args.git_provider,
            args.git_provider_url,
            apps_tmp_dir,
        )

        apps_git.checkout(args.branch)
        shortened_branch_hash = str(int(hashlib.sha256(args.branch.encode("utf-8")).hexdigest(), 16) % 10 ** 8)

        gitops_config = GitOpsConfig(apps_git.get_full_file_path(".gitops.config.yaml"))

        root_git = create_git(
            args.username,
            args.password,
            args.git_user,
            args.git_email,
            gitops_config.team_config_org,
            gitops_config.team_config_repo,
            args.git_provider,
            args.git_provider_url,
            root_tmp_dir,
        )
        root_git.checkout("master")
        root_git.new_branch(args.branch)
        new_preview_folder_name = gitops_config.application_name + "-" + shortened_branch_hash + "-preview"
        preview_template_folder_name = ".preview-templates/" + gitops_config.application_name
        route_host = None
        if not os.path.exists(root_git.get_full_file_path(new_preview_folder_name)):
            shutil.copytree(
                root_git.get_full_file_path(preview_template_folder_name),
                root_git.get_full_file_path(new_preview_folder_name),
            )
            chart_file_path = new_preview_folder_name + "/Chart.yaml"
            if root_git.get_full_file_path(chart_file_path):
                update_yaml_file(root_git.get_full_file_path(chart_file_path), "name", new_preview_folder_name)
                if gitops_config.route_paths:
                    route_host = gitops_config.route_host.replace("previewplaceholder", shortened_branch_hash)
                    for route_path in gitops_config.route_paths:
                        yaml_replace_path = route_path["hostpath"]
                        update_yaml_file(
                            root_git.get_full_file_path(new_preview_folder_name + "/values.yaml"),
                            yaml_replace_path,
                            route_host,
                        )

            root_git.commit(f"Initiated new preview env for branch {args.branch}'")

        new_image_tag = apps_git.get_last_commit_hash()
        for image_path in gitops_config.image_paths:
            yaml_replace_path = image_path["yamlpath"]
            update_yaml_file(
                root_git.get_full_file_path(new_preview_folder_name + "/values.yaml"), yaml_replace_path, new_image_tag,
            )
            root_git.commit(f"changed '{yaml_replace_path}' to '{new_image_tag}'")

        root_git.push(args.branch)
        pr_comment_text = f"""
Preview created successfully. Access it [here](https://{route_host}).
"""
        apps_git.add_pull_request_comment(args.pr_id, pr_comment_text, args.parent_id)

    finally:
        shutil.rmtree(apps_tmp_dir, ignore_errors=True)
        shutil.rmtree(root_tmp_dir, ignore_errors=True)

    if args.create_pr and args.branch != "master":
        title = "Updated preview environemnt for " + gitops_config.application_name
        description = f"""
This Pull Request is automatically created through [gitopscli](https://github.com/baloise-incubator/gitopscli).
"""
        pull_request = root_git.create_pull_request(args.branch, "master", title, description)
        print(f"Pull request created: {root_git.get_pull_request_url(pull_request)}")

        if args.auto_merge:
            root_git.merge_pull_request(pull_request)
            print("Pull request merged")

            root_git.delete_branch(args.branch)
            print(f"Branch '{args.branch}' deleted")


def main():
    logging.basicConfig(level=logging.INFO)

    parser, subparsers = create_cli_parser()
    add_deploy_parser(subparsers)
    add_sync_apps_parser(subparsers)
    add_pr_comment_parser(subparsers)
    add_create_preview_parser(subparsers)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    if args.command == "deploy":
        deploy(**vars(args))

    if args.command == "sync-apps":
        sync_apps_command(args)

    if args.command == "add-pr-comment":
        pr_comment_command(args)

    if args.command == "create-preview":
        create_preview_command(args)


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

    add_git_parser_args(deploy_p)


def add_git_parser_args(deploy_p):
    deploy_p.add_argument("-b", "--branch", help="Branch to push the changes to", default="master")
    deploy_p.add_argument("-u", "--username", help="Git username if Basic Auth should be used")
    deploy_p.add_argument("-p", "--password", help="Git password if Basic Auth should be used")
    deploy_p.add_argument("-j", "--git-user", help="Git Username", default="GitOpsCLI")
    deploy_p.add_argument("-e", "--git-email", help="Git User Email", default="gitopscli@baloise.dev")
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
    deploy_p.add_argument("-o", "--organisation", help="Apps Git organisation/projectKey", required=True)
    deploy_p.add_argument(
        "-n", "--repository-name", help="Git repository name (not the URL, e.g. my-repo)", required=True
    )
    deploy_p.add_argument("-s", "--git-provider", help="Git server provider", default="bitbucket-server")
    deploy_p.add_argument(
        "-w", "--git-provider-url", help="Git provider base API URL (e.g. https://bitbucket.example.tld)"
    )


def add_sync_apps_parser(subparsers):
    sync_apps_p = subparsers.add_parser(
        "sync-apps", help="Synchronize applications (= every directory) from apps config repository to apps root config"
    )
    add_git_parser_args(sync_apps_p)
    sync_apps_p.add_argument("-i", "--root-organisation", help="Apps config repository organisation", required=True)
    sync_apps_p.add_argument("-r", "--root-repository-name", help="Root config repository organisation", required=True)


def add_pr_comment_parser(subparsers):
    add_pr_comment_p = subparsers.add_parser("add-pr-comment", help="Create a comment on the pull request")
    add_git_parser_args(add_pr_comment_p)
    add_pr_comment_p.add_argument("-i", "--pr-id", help="the id of the pull request", type=int, required=True)
    add_pr_comment_p.add_argument("-t", "--text", help="the text of the comment", required=True)
    add_pr_comment_p.add_argument(
        "-x", "--parent-id", help="the id of the parent comment, in case of a reply", type=int
    )


def add_create_preview_parser(subparsers):
    add_create_preview_p = subparsers.add_parser("create-preview", help="Create a preview environment")
    add_git_parser_args(add_create_preview_p)
    add_create_preview_p.add_argument("-i", "--pr-id", help="the id of the pull request", type=int, required=True)
    add_create_preview_p.add_argument(
        "-x", "--parent-id", help="the id of the parent comment, in case of a reply", type=int
    )


def deploy(
    command,
    file,
    values,
    branch,
    username,
    password,
    git_user,
    git_email,
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
        git = create_git(
            username,
            password,
            git_user,
            git_email,
            organisation,
            repository_name,
            git_provider,
            git_provider_url,
            tmp_dir,
        )
        git.checkout("master")
        git.new_branch(branch)
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
