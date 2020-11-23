from typing import Optional, NamedTuple
from gitopscli.git import GitApiConfig, GitRepoApiFactory


class AddPrCommentArgs(NamedTuple):
    git_provider: Optional[str]
    git_provider_url: Optional[str]

    username: str
    password: str

    organisation: str
    repository_name: str

    pr_id: int
    parent_id: Optional[int]
    text: str


def pr_comment_command(args: AddPrCommentArgs) -> None:
    git_api_config = GitApiConfig(args.username, args.password, args.git_provider, args.git_provider_url,)
    git_repo_api = GitRepoApiFactory.create(git_api_config, args.organisation, args.repository_name,)
    git_repo_api.add_pull_request_comment(args.pr_id, args.text, args.parent_id)
