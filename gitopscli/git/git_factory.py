import logging
import collections

from gitopscli.gitops_exception import GitOpsException

from .abstract_git_util import AbstractGitUtil
from .bitbucket_git_util import BitBucketGitUtil
from .github_git_util import GithubGitUtil

GitConfig = collections.namedtuple(
    "GitConfig", ["username", "password", "git_user", "git_email", "git_provider", "git_provider_url"]
)


def create_git(git_config: GitConfig, organisation: str, repository_name: str) -> AbstractGitUtil:
    git_provider = git_config.git_provider or __infer_git_provider_from_url(git_config.git_provider_url)
    if git_provider == "bitbucket-server":
        if not git_config.git_provider_url:
            raise GitOpsException("Please provide url for bitbucket-server.")
        git = BitBucketGitUtil(
            git_provider_url=git_config.git_provider_url,
            organisation=organisation,
            repository_name=repository_name,
            username=git_config.username,
            password=git_config.password,
            git_user=git_config.git_user,
            git_email=git_config.git_email,
        )
    elif git_provider == "github":
        git = GithubGitUtil(
            organisation=organisation,
            repository_name=repository_name,
            username=git_config.username,
            password=git_config.password,
            git_user=git_config.git_user,
            git_email=git_config.git_email,
        )
    else:
        raise GitOpsException(f"Git provider '{git_config.git_provider}' is not supported.")
    return git


def __infer_git_provider_from_url(git_provider_url: str) -> str:
    if "bitbucket" in git_provider_url:
        git_provider = "bitbucket-server"
    elif "github" in git_provider_url:
        git_provider = "github"
    else:
        raise GitOpsException(f"Unknown git provider url: '{git_provider_url}'. Please specify git provider.")
    logging.info("Inferred git provider '%s' from url '%s'", git_provider, git_provider_url)
    return git_provider
