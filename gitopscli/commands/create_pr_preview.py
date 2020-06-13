import logging

from gitopscli.commands.create_preview import create_preview_command
from gitopscli.git.create_git import create_git
from gitopscli.io.tmp_dir import create_tmp_dir, delete_tmp_dir


def create_pr_preview_command(
    command,
    pr_id,
    parent_id,
    username,
    password,
    git_user,
    git_email,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
):
    assert command == "create-pr-preview"

    apps_tmp_dir = create_tmp_dir()

    try:
        apps_git = create_git(
            username,
            password,
            git_user,
            git_email,
            organisation,
            repository_name,
            git_provider,
            git_provider_url,
            apps_tmp_dir,
        )

        pr_branch = apps_git.get_pull_request_branch(pr_id)

        apps_git.checkout(pr_branch)
        logging.info("App repo PR branch %s checkout successful", pr_branch)
        git_hash = apps_git.get_last_commit_hash()
        create_preview_command(
            username,
            password,
            git_user,
            git_email,
            organisation,
            repository_name,
            git_provider,
            git_provider_url,
            git_hash,
            pr_branch,  # <- preview_id
            __create_deployment_already_up_to_date_callback(parent_id, pr_id),
            __create_deployment_exist_callback(parent_id, pr_id, pr_branch),
            __create_deployment_new_callback(parent_id, pr_id, pr_branch),
        )
    finally:
        delete_tmp_dir(apps_tmp_dir)


def __create_deployment_already_up_to_date_callback(parent_id, pr_id):
    def deployment_already_up_to_date_callback(apps_git, new_image_tag):
        __add_pull_request_comment(
            apps_git, pr_id, parent_id, f"The version `{new_image_tag}` has already been deployed. Nothing to do here."
        )

    return deployment_already_up_to_date_callback


def __create_deployment_new_callback(parent_id, pr_id, pr_branch):
    def deployment_new_callback(apps_git, gitops_config, route_host):
        app_name = gitops_config.application_name
        __add_pull_request_comment(
            apps_git,
            pr_id,
            parent_id,
            f"""\
New preview environment for `{app_name}` and branch `{pr_branch}` created successfully. Access it here:
https://{route_host}""",
        )

    return deployment_new_callback


def __create_deployment_exist_callback(parent_id, pr_id, pr_branch):
    def deployment_exist_callback(apps_git, gitops_config, route_host):
        app_name = gitops_config.application_name
        __add_pull_request_comment(
            apps_git,
            pr_id,
            parent_id,
            f"""\
Preview environment for `{app_name}` and branch `{pr_branch}` updated successfully. Access it here:
https://{route_host}""",
        )

    return deployment_exist_callback


def __add_pull_request_comment(apps_git, pr_id, parent_id, pr_comment_text):
    logging.info("Creating PullRequest comment for pr with id %s and content: %s", pr_id, pr_comment_text)
    apps_git.add_pull_request_comment(pr_id, pr_comment_text, parent_id)
