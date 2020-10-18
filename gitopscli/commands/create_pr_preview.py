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

        def add_pr_comment(comment):
            logging.info("Adding comment to pull request with id %s: %s", pr_id, comment)
            apps_git.add_pull_request_comment(pr_id, comment, parent_id)

        create_preview_command(
            command="create-preview",
            username=username,
            password=password,
            git_user=git_user,
            git_email=git_email,
            organisation=organisation,
            repository_name=repository_name,
            git_provider=git_provider,
            git_provider_url=git_provider_url,
            git_hash=git_hash,
            preview_id=pr_branch,  # use pr_branch as preview id
            deployment_already_up_to_date_callback=lambda route_host: add_pr_comment(
                f"The version `{git_hash}` has already been deployed. Access it here: https://{route_host}",
            ),
            deployment_exists_callback=lambda route_host: add_pr_comment(
                f"Preview environment updated to version `{git_hash}`. Access it here: https://{route_host}"
            ),
            deployment_new_callback=lambda route_host: add_pr_comment(
                f"New preview environment created for version `{git_hash}`. Access it here: https://{route_host}"
            ),
        )
