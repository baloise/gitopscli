import logging

from gitopscli.git import create_git, GitConfig


def pr_comment_command(
    command, text, username, password, parent_id, pr_id, organisation, repository_name, git_provider, git_provider_url,
):
    assert command == "add-pr-comment"
    with create_git(
        GitConfig(
            username=username,
            password=password,
            git_user=None,
            git_email=None,
            git_provider=git_provider,
            git_provider_url=git_provider_url,
        ),
        organisation,
        repository_name,
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
