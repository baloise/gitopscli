from typing import Any, Literal

from azure.devops.connection import Connection
from azure.devops.credentials import BasicAuthentication
from azure.devops.v7_1.git.models import (
    Comment,
    GitPullRequest,
    GitPullRequestCommentThread,
    GitPullRequestCompletionOptions,
    GitRefUpdate,
)
from msrest.exceptions import ClientException

from gitopscli.gitops_exception import GitOpsException

from .git_repo_api import GitRepoApi


class AzureDevOpsGitRepoApiAdapter(GitRepoApi):
    """Azure DevOps SDK adapter for GitOps CLI operations."""

    def __init__(
        self,
        git_provider_url: str,
        username: str | None,
        password: str | None,
        organisation: str,
        repository_name: str,
    ) -> None:
        # In Azure DevOps:
        # git_provider_url = https://dev.azure.com/organization (e.g. https://dev.azure.com/org)
        # organisation = project name
        # repository_name = repo name
        self.__base_url = git_provider_url.rstrip("/")
        self.__username = username or ""
        self.__password = password
        self.__project_name = organisation  # In Azure DevOps, "organisation" param is actually the project
        self.__repository_name = repository_name

        if not password:
            raise GitOpsException("Password (Personal Access Token) is required for Azure DevOps")

        credentials = BasicAuthentication(self.__username, password)
        self.__connection = Connection(base_url=self.__base_url, creds=credentials)
        self.__git_client = self.__connection.clients.get_git_client()

    def get_username(self) -> str | None:
        return self.__username

    def get_password(self) -> str | None:
        return self.__password

    def get_clone_url(self) -> str:
        # https://dev.azure.com/organization/project/_git/repository
        return f"{self.__base_url}/{self.__project_name}/_git/{self.__repository_name}"

    def create_pull_request_to_default_branch(
        self,
        from_branch: str,
        title: str,
        description: str,
    ) -> GitRepoApi.PullRequestIdAndUrl:
        to_branch = self.__get_default_branch()
        return self.create_pull_request(from_branch, to_branch, title, description)

    def create_pull_request(
        self,
        from_branch: str,
        to_branch: str,
        title: str,
        description: str,
    ) -> GitRepoApi.PullRequestIdAndUrl:
        try:
            source_ref = from_branch if from_branch.startswith("refs/") else f"refs/heads/{from_branch}"
            target_ref = to_branch if to_branch.startswith("refs/") else f"refs/heads/{to_branch}"

            pull_request = GitPullRequest(
                source_ref_name=source_ref,
                target_ref_name=target_ref,
                title=title,
                description=description,
            )

            created_pr = self.__git_client.create_pull_request(
                git_pull_request_to_create=pull_request,
                repository_id=self.__repository_name,
                project=self.__project_name,
            )

            return GitRepoApi.PullRequestIdAndUrl(pr_id=created_pr.pull_request_id, url=created_pr.url)

        except ClientException as ex:
            error_msg = str(ex)
            if "401" in error_msg:
                raise GitOpsException("Bad credentials") from ex
            if "404" in error_msg:
                raise GitOpsException(
                    f"Repository '{self.__project_name}/{self.__repository_name}' does not exist"
                ) from ex
            raise GitOpsException(f"Error creating pull request: {error_msg}") from ex
        except Exception as ex:
            raise GitOpsException(f"Error connecting to '{self.__base_url}'") from ex

    def merge_pull_request(
        self,
        pr_id: int,
        merge_method: Literal["squash", "rebase", "merge"] = "merge",
        merge_parameters: dict[str, Any] | None = None,
    ) -> None:
        try:
            pr = self.__git_client.get_pull_request(
                repository_id=self.__repository_name,
                pull_request_id=pr_id,
                project=self.__project_name,
            )

            completion_options = GitPullRequestCompletionOptions()
            if merge_method == "squash":
                completion_options.merge_strategy = "squash"
            elif merge_method == "rebase":
                completion_options.merge_strategy = "rebase"
            else:  # merge
                completion_options.merge_strategy = "noFastForward"

            if merge_parameters:
                for key, value in merge_parameters.items():
                    setattr(completion_options, key, value)

            pr_update = GitPullRequest(
                status="completed",
                last_merge_source_commit=pr.last_merge_source_commit,
                completion_options=completion_options,
            )

            self.__git_client.update_pull_request(
                git_pull_request_to_update=pr_update,
                repository_id=self.__repository_name,
                pull_request_id=pr_id,
                project=self.__project_name,
            )

        except ClientException as ex:
            error_msg = str(ex)
            if "401" in error_msg:
                raise GitOpsException("Bad credentials") from ex
            if "404" in error_msg:
                raise GitOpsException(f"Pull request with ID '{pr_id}' does not exist") from ex
            raise GitOpsException(f"Error merging pull request: {error_msg}") from ex
        except Exception as ex:
            raise GitOpsException(f"Error connecting to '{self.__base_url}'") from ex

    def add_pull_request_comment(self, pr_id: int, text: str, parent_id: int | None = None) -> None:  # noqa: ARG002
        try:
            comment = Comment(content=text, comment_type="text")
            thread = GitPullRequestCommentThread(
                comments=[comment],
                status="active",
            )

            # Azure DevOps doesn't support direct reply to comments in the same way as other platforms
            # parent_id is ignored for now

            self.__git_client.create_thread(
                comment_thread=thread,
                repository_id=self.__repository_name,
                pull_request_id=pr_id,
                project=self.__project_name,
            )

        except ClientException as ex:
            error_msg = str(ex)
            if "401" in error_msg:
                raise GitOpsException("Bad credentials") from ex
            if "404" in error_msg:
                raise GitOpsException(f"Pull request with ID '{pr_id}' does not exist") from ex
            raise GitOpsException(f"Error adding comment: {error_msg}") from ex
        except Exception as ex:
            raise GitOpsException(f"Error connecting to '{self.__base_url}'") from ex

    def delete_branch(self, branch: str) -> None:
        def _raise_branch_not_found() -> None:
            raise GitOpsException(f"Branch '{branch}' does not exist")

        try:
            refs = self.__git_client.get_refs(
                repository_id=self.__repository_name,
                project=self.__project_name,
                filter=f"heads/{branch}",
            )

            if not refs:
                _raise_branch_not_found()

            branch_ref = refs[0]

            # Create ref update to delete the branch
            ref_update = GitRefUpdate(
                name=f"refs/heads/{branch}",
                old_object_id=branch_ref.object_id,
                new_object_id="0000000000000000000000000000000000000000",
            )

            self.__git_client.update_refs(
                ref_updates=[ref_update],
                repository_id=self.__repository_name,
                project=self.__project_name,
            )

        except GitOpsException:
            raise
        except ClientException as ex:
            error_msg = str(ex)
            if "401" in error_msg:
                raise GitOpsException("Bad credentials") from ex
            if "404" in error_msg:
                raise GitOpsException(f"Branch '{branch}' does not exist") from ex
            raise GitOpsException(f"Error deleting branch: {error_msg}") from ex
        except Exception as ex:
            raise GitOpsException(f"Error connecting to '{self.__base_url}'") from ex

    def get_branch_head_hash(self, branch: str) -> str:
        def _raise_branch_not_found() -> None:
            raise GitOpsException(f"Branch '{branch}' does not exist")

        try:
            refs = self.__git_client.get_refs(
                repository_id=self.__repository_name,
                project=self.__project_name,
                filter=f"heads/{branch}",
            )

            if not refs:
                _raise_branch_not_found()

            return str(refs[0].object_id)

        except GitOpsException:
            raise
        except ClientException as ex:
            error_msg = str(ex)
            if "401" in error_msg:
                raise GitOpsException("Bad credentials") from ex
            if "404" in error_msg:
                raise GitOpsException(f"Branch '{branch}' does not exist") from ex
            raise GitOpsException(f"Error getting branch hash: {error_msg}") from ex
        except Exception as ex:
            raise GitOpsException(f"Error connecting to '{self.__base_url}'") from ex

    def get_pull_request_branch(self, pr_id: int) -> str:
        try:
            pr = self.__git_client.get_pull_request(
                repository_id=self.__repository_name,
                pull_request_id=pr_id,
                project=self.__project_name,
            )

            source_ref = str(pr.source_ref_name)
            if source_ref.startswith("refs/heads/"):
                return source_ref[11:]  # Remove "refs/heads/" prefix
            return source_ref

        except ClientException as ex:
            error_msg = str(ex)
            if "401" in error_msg:
                raise GitOpsException("Bad credentials") from ex
            if "404" in error_msg:
                raise GitOpsException(f"Pull request with ID '{pr_id}' does not exist") from ex
            raise GitOpsException(f"Error getting pull request: {error_msg}") from ex
        except Exception as ex:
            raise GitOpsException(f"Error connecting to '{self.__base_url}'") from ex

    def add_pull_request_label(self, pr_id: int, pr_labels: list[str]) -> None:
        # Azure DevOps uses labels differently than other platforms
        # The SDK doesn't have direct label support for pull requests
        # This operation is silently ignored as labels aren't critical for GitOps operations
        pass

    def __get_default_branch(self) -> str:
        try:
            repo = self.__git_client.get_repository(
                repository_id=self.__repository_name,
                project=self.__project_name,
            )

            default_branch = repo.default_branch or "refs/heads/main"
            if default_branch.startswith("refs/heads/"):
                return default_branch[11:]
            return default_branch

        except ClientException as ex:
            error_msg = str(ex)
            if "401" in error_msg:
                raise GitOpsException("Bad credentials") from ex
            if "404" in error_msg:
                raise GitOpsException(
                    f"Repository '{self.__project_name}/{self.__repository_name}' does not exist"
                ) from ex
            raise GitOpsException(f"Error getting repository info: {error_msg}") from ex
        except Exception as ex:
            raise GitOpsException(f"Error connecting to '{self.__base_url}'") from ex
