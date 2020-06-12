import hashlib
import logging
import os
import uuid

from gitopscli.commands.create_preview import create_preview_command
from gitopscli.git.create_git import create_git
from gitopscli.io.tmp_dir import create_tmp_dir, delete_tmp_dir

# pylint: disable=too-many-statements


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
    root_tmp_dir = create_tmp_dir()

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
        preview_id = hashlib.sha256(pr_branch.encode("utf-8")).hexdigest()[:8]
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
            preview_id,
            create_deployment_replaced_callback(parent_id, pr_id),
            create_deployment_exist_callback(parent_id, pr_id, pr_branch),
            create_deployment_new_callback(parent_id, pr_id, pr_branch),
        )
    finally:
        delete_tmp_dir(apps_tmp_dir)
        delete_tmp_dir(root_tmp_dir)


def create_deployment_replaced_callback(parent_id, pr_id):
    def deployment_replaced_callback(apps_git, new_image_tag):
        logging.info("The image tag %s has already been deployed. Doing nothing.", new_image_tag)
        pr_comment_text = f"""
        The version `{new_image_tag}` has already been deployed. Nothing to do here.
        """
        logging.info("Creating PullRequest comment for pr with id %s and content: %s", pr_id, pr_comment_text)
        apps_git.add_pull_request_comment(pr_id, pr_comment_text, parent_id)

    return deployment_replaced_callback


def create_deployment_new_callback(parent_id, pr_id, pr_branch):
    def deployment_new_callback(apps_git, gitops_config, route_host):
        pr_comment_text = f"""
        New preview environment for `{gitops_config.application_name}` and branch `{pr_branch}` created successfully. Access it here:
        https://{route_host}
        """
        logging.info("Creating PullRequest comment for pr with id %s and content: %s", pr_id, pr_comment_text)
        apps_git.add_pull_request_comment(pr_id, pr_comment_text, parent_id)

    return deployment_new_callback


def create_deployment_exist_callback(parent_id, pr_id, pr_branch):
    def deployment_exist_callback(apps_git, gitops_config, route_host):
        pr_comment_text = f"""
        Preview environment for `{gitops_config.application_name}` and branch `{pr_branch}` updated successfully. Access it here:
        https://{route_host}
        """
        logging.info("Creating PullRequest comment for pr with id %s and content: %s", pr_id, pr_comment_text)
        apps_git.add_pull_request_comment(pr_id, pr_comment_text, parent_id)

    return deployment_exist_callback


def __create_pullrequest(branch, gitops_config, root_git):
    title = "Updated preview environment for " + gitops_config.application_name
    description = f"""
This Pull Request is automatically created through [gitopscli](https://github.com/baloise/gitopscli).
"""
    pull_request = root_git.create_pull_request(branch, "master", title, description)
    logging.info("Pull request created: %s", {root_git.get_pull_request_url(pull_request)})
    return pull_request


def __merge_pullrequest(branch, pull_request, root_git):
    root_git.merge_pull_request(pull_request)
    logging.info("Pull request merged")
    root_git.delete_branch(branch)
    logging.info("Branch '%s' deleted", branch)


def __create_tmp_dir():
    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(tmp_dir)
    logging.info("Created directory %s", tmp_dir)
    return tmp_dir
