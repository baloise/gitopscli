from typing import Optional, Literal

from atlassian.bitbucket import Cloud
from atlassian.bitbucket.cloud.repositories import Repository
from gitopscli.gitops_exception import GitOpsException

from .git_repo_api import GitRepoApi

# pylint: disable=fixme
# TODO: remove this pylint comment
class BitbucketCloudGitRepoApiAdapter(GitRepoApi):
    def __init__(
        self,
        username: Optional[str],
        password: Optional[str],
        organisation: str,
        repository_name: str,
    ) -> None:
        self.__cloud = Cloud(username=username, password=password)
        self.__organisation = organisation
        self.__repository_name = repository_name

    def get_username(self) -> Optional[str]:
        return str(self.__cloud.username)

    def get_password(self) -> Optional[str]:
        return str(self.__cloud.password)

    def get_clone_url(self) -> str:
        repo = self.__get_repository()

        # TODO: error handling
        # if "errors" in repo:
        #    for error in repo["errors"]:
        #        exception = error["exceptionName"]
        #        if exception == "com.atlassian.bitbucket.auth.IncorrectPasswordAuthenticationException":
        #            raise GitOpsException("Bad credentials")
        #        if exception == "com.atlassian.bitbucket.project.NoSuchProjectException":
        #            raise GitOpsException(f"Organisation '{self.__organisation}' does not exist")
        #        if exception == "com.atlassian.bitbucket.repository.NoSuchRepositoryException":
        #           raise GitOpsException(f"Repository '{self.__organisation}/{self.__repository_name}' does not exist")
        #        raise GitOpsException(error["message"])

        for clone_link in repo.get_data("links")["clone"]:
            if clone_link["name"] == "https":
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
        pull_request = self.__get_repository().pullrequests.create(
            title,
            from_branch,
            to_branch,
            description,
        )
        # TODO: error handling
        # if "errors" in pull_request:
        #    raise GitOpsException(pull_request["errors"][0]["message"])
        return GitRepoApi.PullRequestIdAndUrl(
            pr_id=pull_request.id, url="foo"
        )  # TODO: get url from pull_request object

    def merge_pull_request(self, pr_id: int, merge_method: Literal["squash", "rebase", "merge"] = "merge") -> None:
        # TODO: implement
        # pull_request = self.__cloud.get_pullrequest(self.__organisation, self.__repository_name, pr_id)
        # self.__cloud.merge_pull_request(
        #    self.__organisation, self.__repository_name, pull_request["id"], pull_request["version"]
        # )
        pass

    def add_pull_request_comment(self, pr_id: int, text: str, parent_id: Optional[int] = None) -> None:
        # TODO: implement
        # pull_request_comment = self.__cloud.add_pull_request_comment(
        #    self.__organisation, self.__repository_name, pr_id, text, parent_id
        # )
        # if "errors" in pull_request_comment:
        #    raise GitOpsException(pull_request_comment["errors"][0]["message"])
        pass

    def delete_branch(self, branch: str) -> None:
        # TODO: implement
        # branch_hash = self.get_branch_head_hash(branch)
        # result = self.__cloud.delete_branch(self.__organisation, self.__repository_name, branch, branch_hash)
        # if result and "errors" in result:
        #    raise GitOpsException(result["errors"][0]["message"])
        pass

    def get_branch_head_hash(self, branch: str) -> str:
        # TODO: implement
        # branches = self.__cloud.get_branches(self.__organisation, self.__repository_name, filter=branch, limit=1)
        # if not branches:
        #    raise GitOpsException(f"Branch '{branch}' not found'")
        # return str(branches[0]["latestCommit"])
        pass

    def get_pull_request_branch(self, pr_id: int) -> str:
        # TODO: implement
        # pull_request = self.__cloud.get_pullrequest(self.__organisation, self.__repository_name, pr_id)
        # if "errors" in pull_request:
        #    raise GitOpsException(pull_request["errors"][0]["message"])
        # return str(pull_request["fromRef"]["displayId"])
        pass

    def __get_default_branch(self) -> str:
        return str(self.__get_repository().get_data("mainbranch")["name"])

    def __get_repository(self) -> Repository:
        return self.__cloud.repositories.get(self.__organisation, self.__repository_name)
