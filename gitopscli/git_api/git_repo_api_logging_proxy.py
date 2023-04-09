import logging
from typing import Any, List, Dict, Optional, Literal
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

    def create_pull_request_to_default_branch(
        self, from_branch: str, title: str, description: str
    ) -> GitRepoApi.PullRequestIdAndUrl:
        logging.info("Creating pull request from '%s' to default branch with title: %s", from_branch, title)
        return self.__api.create_pull_request_to_default_branch(from_branch, title, description)

    def create_pull_request(
        self, from_branch: str, to_branch: str, title: str, description: str
    ) -> GitRepoApi.PullRequestIdAndUrl:
        logging.info("Creating pull request from '%s' to '%s' with title: %s", from_branch, to_branch, title)
        return self.__api.create_pull_request(from_branch, to_branch, title, description)

    def merge_pull_request(
        self,
        pr_id: int,
        merge_method: Literal["squash", "rebase", "merge"] = "merge",
        merge_parameters: Dict[str, Any] = None,
    ) -> None:
        logging.info("Merging pull request %s", pr_id)
        self.__api.merge_pull_request(pr_id, merge_method=merge_method)

    def add_pull_request_comment(self, pr_id: int, text: str, parent_id: Optional[int] = None) -> None:
        if parent_id:
            logging.info(
                "Creating comment for pull request %s as reply to comment %s with content: %s", pr_id, parent_id, text
            )
        else:
            logging.info("Creating comment for pull request %s with content: %s", pr_id, text)
        self.__api.add_pull_request_comment(pr_id, text, parent_id)

    def delete_branch(self, branch: str) -> None:
        logging.info("Deleting branch '%s'", branch)
        self.__api.delete_branch(branch)

    def get_branch_head_hash(self, branch: str) -> str:
        return self.__api.get_branch_head_hash(branch)

    def get_pull_request_branch(self, pr_id: int) -> str:
        return self.__api.get_pull_request_branch(pr_id)

    def add_pull_request_label(self, pr_id: int, pr_labels: List[str]) -> None:
        logging.info("Adding labels for pull request %s with content: %s", pr_id, pr_labels)
        self.__api.add_pull_request_label(pr_id, pr_labels)
