import logging

from gitopscli.git.bitbucket_git_util import BitBucketGitUtil
from gitopscli.git.github_git_util import GithubGitUtil
from gitopscli.gitops_exception import GitOpsException


def create_git(username, password, git_user, git_email, organisation, repository_name, git_provider, git_provider_url):
    if not git_provider:
        if "bitbucket" in git_provider_url:
            git_provider = "bitbucket-server"
        elif "github" in git_provider_url:
            git_provider = "github"
        else:
            raise GitOpsException("Please provide --git-provider")
        logging.info("Inferred git provider '%s' from url '%s'", git_provider, git_provider_url)

    if git_provider == "bitbucket-server":
        if not git_provider_url:
            raise GitOpsException("Please provide --git-provider-url for bitbucket-server")
        git = BitBucketGitUtil(
            git_provider_url=git_provider_url,
            organisation=organisation,
            repository_name=repository_name,
            username=username,
            password=password,
            git_user=git_user,
            git_email=git_email,
        )
    elif git_provider == "github":
        git = GithubGitUtil(
            organisation=organisation,
            repository_name=repository_name,
            username=username,
            password=password,
            git_user=git_user,
            git_email=git_email,
        )
    else:
        raise GitOpsException(f"Git provider '{git_provider}' is not supported.")

    return git
