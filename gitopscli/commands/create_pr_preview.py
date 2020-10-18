import logging

from gitopscli.commands.create_preview import create_preview_command
from gitopscli.git import create_git, GitConfig


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
    with create_git(
        GitConfig(
            username=username,
            password=password,
            git_user=git_user,
            git_email=git_email,
            git_provider=git_provider,
            git_provider_url=git_provider_url,
        ),
        organisation,
        repository_name,
    ) as apps_git:
        pr_branch = apps_git.get_pull_request_branch(pr_id)

        apps_git.checkout(pr_branch)
        logging.info("App repo PR branch %s checkout successful", pr_branch)
        git_hash = apps_git.get_last_commit_hash()
        create_preview_command(
            command,
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
            __create_deployment_already_up_to_date_callback(apps_git, parent_id, pr_id),
            __create_deployment_exist_callback(apps_git, parent_id, pr_id, pr_branch),
            __create_deployment_new_callback(apps_git, parent_id, pr_id, pr_branch),
        )


def __create_deployment_already_up_to_date_callback(apps_git, parent_id, pr_id):
    def deployment_already_up_to_date_callback(new_image_tag):
        __add_pull_request_comment(
            apps_git, pr_id, parent_id, f"The version `{new_image_tag}` has already been deployed. Nothing to do here."
        )

    return deployment_already_up_to_date_callback


def __create_deployment_new_callback(apps_git, parent_id, pr_id, pr_branch):
    def deployment_new_callback(gitops_config, route_host):
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


def __create_deployment_exist_callback(apps_git, parent_id, pr_id, pr_branch):
    def deployment_exist_callback(gitops_config, route_host):
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
