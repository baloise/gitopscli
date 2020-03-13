import logging

from gitopscli.git.create_git import create_git


def pr_comment_command(
    command, text, username, password, parent_id, pr_id, organisation, repository_name, git_provider, git_provider_url,
):
    assert command == "add-pr-comment"
    apps_git = create_git(
        username, password, None, None, organisation, repository_name, git_provider, git_provider_url, None,
    )
    logging.info(
        "Creating PullRequest comment for pr with id %s and parentComment with id %s and content: %s",
        pr_id,
        parent_id,
        text,
    )
    apps_git.add_pull_request_comment(pr_id, text, parent_id)
