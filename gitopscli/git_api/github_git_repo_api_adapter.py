from typing import Any, Dict, Union, Optional, Literal

from github import (
    Github,
    UnknownObjectException,
    BadCredentialsException,
    GitRef,
    PullRequest,
    Repository,
)

from gitopscli.gitops_exception import GitOpsException
from .git_repo_api import GitRepoApi


class GithubGitRepoApiAdapter(GitRepoApi):
    def __init__(
        self, username: Optional[str], password: Optional[str], organisation: str, repository_name: str
    ) -> None:
        self.__github = Github(username, password)
        self.__username = username
        self.__password = password
        self.__organisation = organisation
        self.__repository_name = repository_name

    def get_username(self) -> Optional[str]:
        return self.__username

    def get_password(self) -> Optional[str]:
        return self.__password

    def get_clone_url(self) -> str:
        return self.__get_repo().clone_url

    def create_pull_request_to_default_branch(
        self, from_branch: str, title: str, description: str
    ) -> GitRepoApi.PullRequestIdAndUrl:
        to_branch = self.__get_repo().default_branch
        return self.create_pull_request(from_branch, to_branch, title, description)

    def create_pull_request(
        self, from_branch: str, to_branch: str, title: str, description: str
    ) -> GitRepoApi.PullRequestIdAndUrl:
        repo = self.__get_repo()
        pull_request = repo.create_pull(title=title, body=description, head=from_branch, base=to_branch)
        return GitRepoApi.PullRequestIdAndUrl(pr_id=pull_request.number, url=pull_request.html_url)

    def merge_pull_request(
        self,
        pr_id: int,
        merge_method: Literal["squash", "rebase", "merge"] = "merge",
        merge_parameters: Dict[str, Any] = None,
    ) -> None:
        pull_request = self.__get_pull_request(pr_id)
        pull_request.merge(merge_method=merge_method)

    def add_pull_request_comment(self, pr_id: int, text: str, parent_id: Optional[int] = None) -> None:
        pull_request = self.__get_pull_request(pr_id)
        pull_request.create_issue_comment(text)

    def delete_branch(self, branch: str) -> None:
        git_ref = self.__get_branch_ref(branch)
        git_ref.delete()

    def get_branch_head_hash(self, branch: str) -> str:
        git_ref = self.__get_branch_ref(branch)
        return git_ref.object.sha

    def get_pull_request_branch(self, pr_id: int) -> str:
        pull_request = self.__get_pull_request(pr_id)
        return pull_request.head.ref

    def __get_branch_ref(self, branch: str) -> GitRef.GitRef:
        repo = self.__get_repo()
        try:
            return repo.get_git_ref(f"heads/{branch}")
        except UnknownObjectException as ex:
            raise GitOpsException(f"Branch '{branch}' does not exist.") from ex

    def __get_pull_request(self, pr_id: int) -> PullRequest.PullRequest:
        repo = self.__get_repo()
        try:
            return repo.get_pull(pr_id)
        except UnknownObjectException as ex:
            raise GitOpsException(f"Pull request with ID '{pr_id}' does not exist.") from ex

    def __get_repo(self) -> Repository.Repository:
        try:
            return self.__github.get_repo(f"{self.__organisation}/{self.__repository_name}")
        except BadCredentialsException as ex:
            raise GitOpsException("Bad credentials") from ex
        except UnknownObjectException as ex:
            raise GitOpsException(
                f"Repository '{self.__organisation}/{self.__repository_name}' does not exist."
            ) from ex

    def add_pull_request_label(self, pr_id: int, pr_labels: Union[str, Any]) -> None:
        pull_request = self.__get_pull_request(pr_id)
        pull_request.set_labels(pr_labels)
