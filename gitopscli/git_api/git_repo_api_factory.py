from typing import Optional
from gitopscli.gitops_exception import GitOpsException
from .git_repo_api import GitRepoApi
from .github_git_repo_api_adapter import GithubGitRepoApiAdapter
from .bitbucket_git_repo_api_adapter import BitbucketGitRepoApiAdapter
from .bitbucket_cloud_git_repo_api_adapter import BitbucketCloudGitRepoApiAdapter
from .gitlab_git_repo_api_adapter import GitlabGitRepoApiAdapter
from .git_repo_api_logging_proxy import GitRepoApiLoggingProxy
from .git_api_config import GitApiConfig
from .git_provider import GitProvider


class GitRepoApiFactory:
    @staticmethod
    def create(config: GitApiConfig, organisation: str, repository_name: str) -> GitRepoApi:
        git_repo_api: Optional[GitRepoApi]
        if config.git_provider is GitProvider.GITHUB:
            git_repo_api = GithubGitRepoApiAdapter(
                username=config.username,
                password=config.password,
                organisation=organisation,
                repository_name=repository_name,
            )
        elif config.git_provider is GitProvider.BITBUCKET:
            if not config.git_provider_url:
                raise GitOpsException("Please provide url for Bitbucket!")
            git_repo_api = BitbucketGitRepoApiAdapter(
                git_provider_url=config.git_provider_url,
                username=config.username,
                password=config.password,
                organisation=organisation,
                repository_name=repository_name,
            )
        elif config.git_provider is GitProvider.BITBUCKET_CLOUD:
            git_repo_api = BitbucketCloudGitRepoApiAdapter(
                username=config.username,
                password=config.password,
                organisation=organisation,
                repository_name=repository_name,
            )
        elif config.git_provider is GitProvider.GITLAB:
            provider_url = config.git_provider_url
            if not provider_url:
                provider_url = "https://www.gitlab.com"
            git_repo_api = GitlabGitRepoApiAdapter(
                git_provider_url=provider_url,
                username=config.username,
                password=config.password,
                organisation=organisation,
                repository_name=repository_name,
            )
        return GitRepoApiLoggingProxy(git_repo_api)
