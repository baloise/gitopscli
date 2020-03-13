from github import Github, UnknownObjectException, BadCredentialsException
from gitopscli.gitops_exception import GitOpsException

from .abstract_git_util import AbstractGitUtil


class GithubGitUtil(AbstractGitUtil):
    def __init__(self, tmp_dir, organisation, repository_name, username, password, git_user, git_email):
        super().__init__(tmp_dir, username, password, git_user, git_email)
        self._organisation = organisation
        self._repository_name = repository_name
        self._github = Github(self._username, self._password)

    def get_clone_url(self):
        return self.__get_repo().clone_url

    def create_pull_request(self, from_branch, to_branch, title, description):
        repo = self.__get_repo()
        pull_request = repo.create_pull(title=title, body=description, head=from_branch, base=to_branch)
        return pull_request

    def get_pull_request_url(self, pull_request):
        return pull_request.html_url

    def merge_pull_request(self, pull_request):
        pull_request.merge()

    def add_pull_request_comment(self, pr_id, text, parent_id=None):
        repo = self.__get_repo()
        try:
            pull_request = repo.get_pull(pr_id)
        except UnknownObjectException as ex:
            raise GitOpsException(f"Pull request with ID '{pr_id}' does not exist.") from ex
        pr_comment = pull_request.create_issue_comment(text)
        return pr_comment

    def delete_branch(self, branch):
        repo = self.__get_repo()
        try:
            git_ref = repo.get_git_ref(f"heads/{branch}")
        except UnknownObjectException as ex:
            raise GitOpsException(f"Branch '{branch}' does not exist.") from ex
        git_ref.delete()

    def __get_repo(self):
        try:
            return self._github.get_repo(f"{self._organisation}/{self._repository_name}")
        except BadCredentialsException as ex:
            raise GitOpsException("Bad credentials") from ex
        except UnknownObjectException as ex:
            raise GitOpsException(f"Repository '{self._organisation}/{self._repository_name}' does not exist.") from ex
