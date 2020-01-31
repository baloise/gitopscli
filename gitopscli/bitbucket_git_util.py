import sys
from atlassian import Bitbucket
from .abstract_git_util import AbstractGitUtil


class BitBucketGitUtil(AbstractGitUtil):
    def __init__(
        self, tmp_dir, git_provider_url, organisation, repository_name, username, password, git_user, git_password
    ):
        super().__init__(tmp_dir, username, password, git_user, git_password)
        self._git_provider_url = git_provider_url
        self._organisation = organisation
        self._repository_name = repository_name
        self._bitbucket = Bitbucket(self._git_provider_url, self._username, self._password)

    def get_clone_url(self):
        repo = self._bitbucket.get_repo(self._organisation, self._repository_name)
        if "links" not in repo:
            print(
                f"Repository '{self._repository_name}' or organisation '{self._organisation}' does not exist.",
                file=sys.stderr,
            )
            sys.exit(1)
        for clone_link in repo["links"]["clone"]:
            if clone_link["name"] == "http":
                repo_url = clone_link["href"]
        if not repo_url:
            print("Couldn't determine repository URL.", file=sys.stderr)
            sys.exit(1)
        return repo_url

    def create_pull_request(self, from_branch, to_branch, title, description):
        pull_request = self._bitbucket.open_pull_request(
            self._organisation,
            self._repository_name,
            self._organisation,
            self._repository_name,
            from_branch,
            to_branch,
            title,
            description,
        )
        if "errors" in pull_request:
            for error in pull_request["errors"]:
                print(error["message"], file=sys.stderr)
            sys.exit(1)
        return pull_request

    def get_pull_request_url(self, pull_request):
        return pull_request["links"]["self"][0]["href"]

    def merge_pull_request(self, pull_request):
        self._bitbucket.merge_pull_request(
            self._organisation, self._repository_name, pull_request["id"], pull_request["version"]
        )

    def add_pull_request_comment(self, pull_request, text):
        pull_request_comment = self._bitbucket.add_pull_request_comment(
            self._organisation, self._repository_name, pull_request["id"], pull_request["version"]
        )
        if "errors" in self, pull_request_comment:
            for error in pull_request_comment["errors"]:
                print(error["message"], file=sys.stderr)
            sys.exit(1)
        return pull_request_comment

    def delete_branch(self, branch):
        branches = self._bitbucket.get_branches(self._organisation, self._repository_name, filter=branch, limit=1)
        if not branches:
            print(f"Branch '{branch}' not found'", file=sys.stderr)
            sys.exit(1)
        result = self._bitbucket.delete_branch(
            self._organisation, self._repository_name, branch, branches[0]["latestCommit"]
        )
        if result and "errors" in result:
            for error in result["errors"]:
                print(error["message"], file=sys.stderr)
            sys.exit(1)
