import logging

from gitopscli.git import GitApiConfig, GitRepoApiFactory


def pr_comment_command(
    command, text, username, password, parent_id, pr_id, organisation, repository_name, git_provider, git_provider_url,
):
    assert command == "add-pr-comment"
    git_api_config = GitApiConfig(username, password, git_provider, git_provider_url,)
    git_repo_api = GitRepoApiFactory.create(git_api_config, organisation, repository_name,)
    if parent_id:
        logging.info(
            "Creating comment for PR %s as reply to comment %s with content: %s", pr_id, parent_id, text,
        )
    else:
        logging.info(
            "Creating comment for PR %s with content: %s", pr_id, text,
        )
    git_repo_api.add_pull_request_comment(pr_id, text, parent_id)
