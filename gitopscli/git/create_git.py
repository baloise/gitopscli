import logging

from gitopscli.git.bitbucket_git_util import BitBucketGitUtil
from gitopscli.git.github_git_util import GithubGitUtil
from gitopscli.gitops_exception import GitOpsException


def create_git(
    username, password, git_user, git_email, organisation, repository_name, git_provider, git_provider_url, tmp_dir
):
    if not git_provider:
        if "bitbucket" in git_provider_url:
            git_provider = "bitbucket-server"
        elif "github" in git_provider_url:
            git_provider = "github"
        else:
            raise GitOpsException("Please provide --git-provider-url")
        logging.info("Inferred git provider '%s' from url '%s'", git_provider, git_provider_url)

    if git_provider == "bitbucket-server":
        if not git_provider_url:
            raise GitOpsException("Please provide --git-provider-url for bitbucket-server")
        git = BitBucketGitUtil(
            tmp_dir, git_provider_url, organisation, repository_name, username, password, git_user, git_email
        )
    elif git_provider == "github":
        git = GithubGitUtil(tmp_dir, organisation, repository_name, username, password, git_user, git_email)
    else:
        raise GitOpsException(f"Git provider '{git_provider}' is not supported.")

    return git
