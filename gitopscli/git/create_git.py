import sys

from gitopscli.git.bitbucket_git_util import BitBucketGitUtil
from gitopscli.git.github_git_util import GithubGitUtil


def create_git(
        username, password, git_user, git_email, organisation, repository_name, git_provider, git_provider_url, tmp_dir
):
    if git_provider == "bitbucket-server":
        if not git_provider_url:
            print(f"Please provide --git-provider-url for bitbucket-server", file=sys.stderr)
            sys.exit(1)

        git = BitBucketGitUtil(
            tmp_dir, git_provider_url, organisation, repository_name, username, password, git_user, git_email
        )
    elif git_provider == "github":

        git = GithubGitUtil(tmp_dir, organisation, repository_name, username, password, git_user, git_email)
    else:
        print(f"Git provider '{git_provider}' is not supported.", file=sys.stderr)
        sys.exit(1)
    return git
