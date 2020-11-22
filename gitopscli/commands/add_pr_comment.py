from typing import Optional
from gitopscli.git import GitApiConfig, GitRepoApiFactory


def pr_comment_command(
    command: str,
    text: str,
    username: Optional[str],
    password: Optional[str],
    parent_id: Optional[int],
    pr_id: int,
    organisation: str,
    repository_name: str,
    git_provider: Optional[str],
    git_provider_url: Optional[str],
) -> None:
    assert command == "add-pr-comment"
    git_api_config = GitApiConfig(username, password, git_provider, git_provider_url,)
    git_repo_api = GitRepoApiFactory.create(git_api_config, organisation, repository_name,)
    git_repo_api.add_pull_request_comment(pr_id, text, parent_id)
