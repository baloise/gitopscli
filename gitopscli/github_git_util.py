import sys
from github import Github, UnknownObjectException
from .abstract_git_util import AbstractGitUtil


class GithubGitUtil(AbstractGitUtil):
    def __init__(self, tmp_dir, organisation, repository_name, username, password):
        super().__init__(tmp_dir, username, password)
        self._organisation = organisation
        self._repository_name = repository_name
        self._github = Github(self._username, self._password)

    def get_clone_url(self):
        try:
            repo = self._github.get_repo(f"{self._organisation}/{self._repository_name}")
        except UnknownObjectException:
            print(
                f"Repository '{self._organisation}/{self._repository_name}' does not exist.", file=sys.stderr,
            )
            sys.exit(1)
        return repo.clone_url

    def create_pull_request(self, from_branch, to_branch, title, description):
        repo = self._github.get_repo(f"{self._organisation}/{self._repository_name}")
        pull_request = repo.create_pull(title=title, body=description, head=from_branch, base=to_branch)
        return pull_request

    def get_pull_request_url(self, pull_request):
        return pull_request.html_url

    def merge_pull_request(self, pull_request):
        pull_request.merge()
