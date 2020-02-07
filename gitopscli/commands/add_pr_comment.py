import logging
import os
import shutil
import uuid

from gitopscli.git.create_git import create_git


def pr_comment_command(
    command,
    text,
    username,
    password,
    git_user,
    git_email,
    parent_id,
    pr_id,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
):
    assert command == "add-pr-comment"

    apps_tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(apps_tmp_dir)
    logging.info("Created directory %s", apps_tmp_dir)

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

        logging.info(
            "Creating PullRequest comment for pr with id %s and parentComment with id %s and content: %s",
            pr_id,
            text,
            parent_id,
        )
        apps_git.add_pull_request_comment(pr_id, text, parent_id)
    finally:
        shutil.rmtree(apps_tmp_dir, ignore_errors=True)
