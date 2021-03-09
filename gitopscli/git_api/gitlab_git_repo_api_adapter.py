from typing import Optional
import logging
import time
import requests

import gitlab
from gitopscli.gitops_exception import GitOpsException

from .git_repo_api import GitRepoApi

MAX_MERGE_RETRIES = 5


class GitlabGitRepoApiAdapter(GitRepoApi):
    def __init__(
        self,
        git_provider_url: str,
        username: Optional[str],
        password: Optional[str],
        organisation: str,
        repository_name: str,
    ) -> None:
        try:
            self.__gitlab = gitlab.Gitlab(git_provider_url, private_token=password)
            project = self.__gitlab.projects.get(f"{organisation}/{repository_name}")
        except requests.exceptions.ConnectionError as ex:
            raise GitOpsException(f"Error connecting to '{git_provider_url}''") from ex
        except gitlab.exceptions.GitlabAuthenticationError as ex:
            raise GitOpsException("Bad Personal Access Token")
        except gitlab.exceptions.GitlabGetError as ex:
            if ex.response_code == 404:
                raise GitOpsException(f"Repository '{organisation}/{repository_name}' does not exist")
            raise GitOpsException(f"Error getting repository: '{ex.error_message}'")

        self.__token_name = username
        self.__access_token = password
        self.__project = project

    def get_username(self) -> Optional[str]:
        return self.__token_name

    def get_password(self) -> Optional[str]:
        return self.__access_token

    def get_clone_url(self) -> str:
        return str(self.__project.http_url_to_repo)

    def create_pull_request_to_default_branch(
        self, from_branch: str, title: str, description: str
    ) -> GitRepoApi.PullRequestIdAndUrl:
        to_branch = self.__get_default_branch()
        return self.create_pull_request(from_branch, to_branch, title, description)

    def create_pull_request(
        self, from_branch: str, to_branch: str, title: str, description: str
    ) -> GitRepoApi.PullRequestIdAndUrl:
        merge_request = self.__project.mergerequests.create(
            {"source_branch": from_branch, "target_branch": to_branch, "title": title, "description": description}
        )
        return GitRepoApi.PullRequestIdAndUrl(pr_id=merge_request.iid, url=merge_request.web_url)

    def merge_pull_request(self, pr_id: int) -> None:
        merge_request = self.__project.mergerequests.get(pr_id)

        max_retries = MAX_MERGE_RETRIES
        while max_retries > 0:
            try:
                logging.info("(%s/%s) Trying to merge ...", (MAX_MERGE_RETRIES - max_retries) + 1, MAX_MERGE_RETRIES)
                merge_request.merge()
                return
            except gitlab.exceptions.GitlabMRClosedError:
                # "Branch cannot be merged" error can occur if the server
                # is still processing the merge request internally"""
                max_retries -= 1
                time.sleep(2.5)

        raise GitOpsException("Error merging pull request: 'Branch cannot be merged'")

    def add_pull_request_comment(self, pr_id: int, text: str, parent_id: Optional[int] = None) -> None:
        merge_request = self.__project.mergerequests.get(pr_id)
        merge_request.notes.create({"body": text})

    def delete_branch(self, branch: str) -> None:
        self.__project.branches.delete(branch)

    def get_branch_head_hash(self, branch: str) -> str:
        branch_instance = self.__project.branches.get(branch)
        return str(branch_instance.commit["id"])

    def get_pull_request_branch(self, pr_id: int) -> str:
        merge_request = self.__project.mergerequests.get(pr_id)
        return str(merge_request.source_branch)

    def __get_default_branch(self) -> str:
        branches = self.__project.branches.list()
        default_branch = next(filter(lambda x: x.default, branches), None)
        if default_branch is None:
            raise GitOpsException(f"Default branch does not exist")
        return str(default_branch.name)
