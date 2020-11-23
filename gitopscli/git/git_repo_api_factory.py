from gitopscli.gitops_exception import GitOpsException
from .git_repo_api import GitRepoApi
from .github_git_repo_api_adapter import GithubGitRepoApiAdapter
from .bitbucket_git_repo_api_adapter import BitbucketGitRepoApiAdapter
from .git_repo_api_logging_proxy import GitRepoApiLoggingProxy

from .git_api_config import GitApiConfig


class GitRepoApiFactory:
    @staticmethod
    def create(config: GitApiConfig, organisation: str, repository_name: str) -> GitRepoApi:
        git_repo_api: GitRepoApi
        if config.is_provider_github:
            git_repo_api = GithubGitRepoApiAdapter(
                username=config.username,
                password=config.password,
                organisation=organisation,
                repository_name=repository_name,
            )
        elif config.is_provider_bitbucket:
            if not config.git_provider_url:
                raise GitOpsException("Please provide url for bitbucket!")
            git_repo_api = BitbucketGitRepoApiAdapter(
                git_provider_url=config.git_provider_url,
                username=config.username,
                password=config.password,
                organisation=organisation,
                repository_name=repository_name,
            )
        else:
            raise GitOpsException(f"Unknown git provider: {config.git_provider}")
        return GitRepoApiLoggingProxy(git_repo_api)
