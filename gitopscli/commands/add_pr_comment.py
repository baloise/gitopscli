import logging

from gitopscli.git.create_git import create_git


def pr_comment_command(
    command, text, username, password, parent_id, pr_id, organisation, repository_name, git_provider, git_provider_url,
):
    assert command == "add-pr-comment"
    with create_git(
        username, password, None, None, organisation, repository_name, git_provider, git_provider_url,
    ) as apps_git:
        if parent_id:
            logging.info(
                "Creating comment for PR %s as reply to comment %s with content: %s", pr_id, parent_id, text,
            )
        else:
            logging.info(
                "Creating comment for PR %s with content: %s", pr_id, text,
            )
        apps_git.add_pull_request_comment(pr_id, text, parent_id)
