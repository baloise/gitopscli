from gitopscli.cli import AddPrCommentArgs
from gitopscli.git import GitApiConfig, GitRepoApiFactory


def pr_comment_command(args: AddPrCommentArgs) -> None:
    git_api_config = GitApiConfig(args.username, args.password, args.git_provider, args.git_provider_url,)
    git_repo_api = GitRepoApiFactory.create(git_api_config, args.organisation, args.repository_name,)
    git_repo_api.add_pull_request_comment(args.pr_id, args.text, args.parent_id)
