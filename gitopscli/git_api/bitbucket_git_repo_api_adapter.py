from typing import List, Dict, Any, Optional, Literal
import requests

from atlassian import Bitbucket
from gitopscli.gitops_exception import GitOpsException

from .git_repo_api import GitRepoApi


class BitbucketGitRepoApiAdapter(GitRepoApi):
    def __init__(
        self,
        git_provider_url: str,
        username: Optional[str],
        password: Optional[str],
        organisation: str,
        repository_name: str,
    ) -> None:
        self.__bitbucket = Bitbucket(git_provider_url, username, password)
        self.__git_provider_url = git_provider_url
        self.__organisation = organisation
        self.__repository_name = repository_name

    def get_username(self) -> Optional[str]:
        return str(self.__bitbucket.username)

    def get_password(self) -> Optional[str]:
        return str(self.__bitbucket.password)

    def get_clone_url(self) -> str:
        try:
            repo = self.__bitbucket.get_repo(self.__organisation, self.__repository_name)
        except requests.exceptions.ConnectionError as ex:
            raise GitOpsException(f"Error connecting to '{self.__git_provider_url}''") from ex
        if "errors" in repo:
            for error in repo["errors"]:
                exception = error["exceptionName"]
                if exception == "com.atlassian.bitbucket.auth.IncorrectPasswordAuthenticationException":
                    raise GitOpsException("Bad credentials")
                if exception == "com.atlassian.bitbucket.project.NoSuchProjectException":
                    raise GitOpsException(f"Organisation '{self.__organisation}' does not exist")
                if exception == "com.atlassian.bitbucket.repository.NoSuchRepositoryException":
                    raise GitOpsException(f"Repository '{self.__organisation}/{self.__repository_name}' does not exist")
                raise GitOpsException(error["message"])
        if "links" not in repo:
            raise GitOpsException(f"Repository '{self.__organisation}/{self.__repository_name}' does not exist")
        for clone_link in repo["links"]["clone"]:
            if clone_link["name"] == "http":
                repo_url = clone_link["href"]
        if not repo_url:
            raise GitOpsException("Couldn't determine repository URL.")
        return str(repo_url)

    def create_pull_request_to_default_branch(
        self, from_branch: str, title: str, description: str
    ) -> GitRepoApi.PullRequestIdAndUrl:
        to_branch = self.__get_default_branch()
        return self.create_pull_request(from_branch, to_branch, title, description)

    def create_pull_request(
        self, from_branch: str, to_branch: str, title: str, description: str
    ) -> GitRepoApi.PullRequestIdAndUrl:
        pull_request = self.__bitbucket.open_pull_request(
            self.__organisation,
            self.__repository_name,
            self.__organisation,
            self.__repository_name,
            from_branch,
            to_branch,
            title,
            description,
        )
        if "errors" in pull_request:
            raise GitOpsException(pull_request["errors"][0]["message"])
        return GitRepoApi.PullRequestIdAndUrl(pr_id=pull_request["id"], url=pull_request["links"]["self"][0]["href"])

    def merge_pull_request(
        self,
        pr_id: int,
        merge_method: Literal["squash", "rebase", "merge"] = "merge",
        merge_parameters: Dict[str, Any] = None,
    ) -> None:
        pull_request = self.__bitbucket.get_pullrequest(self.__organisation, self.__repository_name, pr_id)
        self.__bitbucket.merge_pull_request(
            self.__organisation, self.__repository_name, pull_request["id"], pull_request["version"]
        )

    def add_pull_request_comment(self, pr_id: int, text: str, parent_id: Optional[int] = None) -> None:
        pull_request_comment = self.__bitbucket.add_pull_request_comment(
            self.__organisation, self.__repository_name, pr_id, text, parent_id
        )
        if "errors" in pull_request_comment:
            raise GitOpsException(pull_request_comment["errors"][0]["message"])

    def delete_branch(self, branch: str) -> None:
        branch_hash = self.get_branch_head_hash(branch)
        result = self.__bitbucket.delete_branch(self.__organisation, self.__repository_name, branch, branch_hash)
        if result and "errors" in result:
            raise GitOpsException(result["errors"][0]["message"])

    def get_branch_head_hash(self, branch: str) -> str:
        branches = self.__bitbucket.get_branches(self.__organisation, self.__repository_name, filter=branch, limit=1)
        if not branches:
            raise GitOpsException(f"Branch '{branch}' not found'")
        return str(branches[0]["latestCommit"])

    def get_pull_request_branch(self, pr_id: int) -> str:
        pull_request = self.__bitbucket.get_pullrequest(self.__organisation, self.__repository_name, pr_id)
        if "errors" in pull_request:
            raise GitOpsException(pull_request["errors"][0]["message"])
        return str(pull_request["fromRef"]["displayId"])

    def __get_default_branch(self) -> str:
        default_branch = self.__bitbucket.get_default_branch(self.__organisation, self.__repository_name)
        return str(default_branch["id"])

    def add_pull_request_label(self, pr_id: int, pr_labels: List[str]) -> None:
        pass
