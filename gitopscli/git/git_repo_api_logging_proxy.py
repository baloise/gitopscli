from typing import Optional
from .git_repo_api import GitRepoApi


class GitRepoApiLoggingProxy(GitRepoApi):
    def __init__(self, git_repo_api: GitRepoApi) -> None:
        self.__api = git_repo_api

    def get_username(self) -> Optional[str]:
        return self.__api.get_username()

    def get_password(self) -> Optional[str]:
        return self.__api.get_password()

    def get_clone_url(self) -> str:
        return self.__api.get_clone_url()

    def create_pull_request(
        self, from_branch: str, to_branch: str, title: str, description: str
    ) -> GitRepoApi.PullRequestIdAndUrl:
        return self.__api.create_pull_request(from_branch, to_branch, title, description)

    def merge_pull_request(self, pr_id: str) -> None:
        self.__api.merge_pull_request(pr_id)

    def add_pull_request_comment(self, pr_id: str, text: str, parent_id: Optional[str] = None) -> None:
        self.__api.add_pull_request_comment(pr_id, text, parent_id)

    def delete_branch(self, branch: str) -> None:
        self.__api.delete_branch(branch)

    def get_branch_head_hash(self, branch: str) -> str:
        return self.__api.get_branch_head_hash(branch)

    def get_pull_request_branch(self, pr_id: str) -> str:
        return self.__api.get_pull_request_branch(pr_id)
