import os
import logging
from types import TracebackType
from typing import Optional, Type, Literal
from git import Repo, GitError, GitCommandError
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io_api.tmp_dir import create_tmp_dir, delete_tmp_dir
from .git_repo_api import GitRepoApi


class GitRepo:
    def __init__(self, git_repo_api: GitRepoApi) -> None:
        self.__api = git_repo_api
        self.__repo: Optional[Repo] = None
        self.__tmp_dir: Optional[str] = None

    def __enter__(self) -> "GitRepo":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        self.finalize()
        return False

    def finalize(self) -> None:
        self.__delete_tmp_dir()

    def get_full_file_path(self, relative_path: str) -> str:
        repo = self.__get_repo()
        return os.path.join(repo.working_dir, relative_path)

    def get_clone_url(self) -> str:
        return self.__api.get_clone_url()

    def clone(self, branch: Optional[str] = None) -> None:
        self.__delete_tmp_dir()
        self.__tmp_dir = create_tmp_dir()
        git_options = []
        url = self.get_clone_url()
        if branch:
            logging.info("Cloning repository: %s (branch: %s)", url, branch)
        else:
            logging.info("Cloning repository: %s", url)
        username = self.__api.get_username()
        password = self.__api.get_password()
        try:
            if username is not None and password is not None:
                credentials_file = self.__create_credentials_file(username, password)
                git_options.append(f"--config credential.helper={credentials_file}")
            if branch:
                git_options.append(f"--branch {branch}")
            self.__repo = Repo.clone_from(url=url, to_path=f"{self.__tmp_dir}/repo", multi_options=git_options)
        except GitError as ex:
            if branch:
                raise GitOpsException(f"Error cloning branch '{branch}' of '{url}'") from ex
            raise GitOpsException(f"Error cloning '{url}'") from ex

    def new_branch(self, branch: str) -> None:
        logging.info("Creating new branch: %s", branch)
        repo = self.__get_repo()
        try:
            repo.git.checkout("-b", branch)
        except GitError as ex:
            raise GitOpsException(f"Error creating new branch '{branch}'.") from ex

    def commit(self, git_user: str, git_email: str, message: str) -> Optional[str]:
        repo = self.__get_repo()
        try:
            repo.git.add("--all")
            if repo.index.diff("HEAD"):
                logging.info("Creating commit with message: %s", message)
                repo.config_writer().set_value("user", "name", git_user).release()
                repo.config_writer().set_value("user", "email", git_email).release()
                repo.git.commit("-m", message, "--author", f"{git_user} <{git_email}>")
                return str(repo.head.commit.hexsha)
        except GitError as ex:
            raise GitOpsException("Error creating commit.") from ex
        return None

    def push(self, branch: Optional[str] = None) -> None:
        repo = self.__get_repo()
        if not branch:
            branch = repo.git.branch("--show-current")
        logging.info("Pushing branch: %s", branch)
        try:
            repo.git.push("--set-upstream", "origin", branch)
        except GitCommandError as ex:
            raise GitOpsException(f"Error pushing branch '{branch}' to origin: {ex.stderr}") from ex
        except GitError as ex:
            raise GitOpsException(f"Error pushing branch '{branch}' to origin.") from ex

    def get_author_from_last_commit(self) -> str:
        repo = self.__get_repo()
        last_commit = repo.head.commit
        return str(repo.git.show("-s", "--format=%an <%ae>", last_commit.hexsha))

    def __delete_tmp_dir(self) -> None:
        if self.__tmp_dir:
            delete_tmp_dir(self.__tmp_dir)

    def __get_repo(self) -> Repo:
        if self.__repo:
            return self.__repo
        raise GitOpsException("Repository not cloned yet!")

    def __create_credentials_file(self, username: str, password: str) -> str:
        file_path = f"{self.__tmp_dir}/credentials.sh"
        with open(file_path, "w") as text_file:
            text_file.write("#!/bin/sh\n")
            text_file.write(f"echo username='{username}'\n")
            text_file.write(f"echo password='{password}'\n")
        os.chmod(file_path, 0o700)
        return file_path
