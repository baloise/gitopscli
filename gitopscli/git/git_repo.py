import os
from pathlib import Path
from git import Repo, GitError, GitCommandError

from gitopscli.gitops_exception import GitOpsException
from gitopscli.io.tmp_dir import create_tmp_dir, delete_tmp_dir
from .git_repo_api import GitRepoApi


class GitRepo:
    def __init__(self, git_repo_api: GitRepoApi):
        self.__api = git_repo_api
        self.__repo = None
        self.__tmp_dir = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()

    def finalize(self):
        self.__delete_tmp_dir()

    def get_full_file_path(self, relative_path):
        return Path(os.path.join(self.__repo.working_dir, relative_path))

    def get_clone_url(self):
        return self.__api.get_clone_url()

    def checkout(self, branch):
        self.__delete_tmp_dir()
        self.__tmp_dir = create_tmp_dir()
        git_options = []
        url = self.get_clone_url()
        username = self.__api.get_username()
        password = self.__api.get_password()
        try:
            if username is not None and password is not None:
                credentials_file = self.__create_credentials_file(username, password)
                git_options.append(f"--config credential.helper={credentials_file}")
            self.__repo = Repo.clone_from(url=url, to_path=f"{self.__tmp_dir}/repo", multi_options=git_options)
        except GitError as ex:
            raise GitOpsException(f"Error cloning '{url}'") from ex
        try:
            self.__repo.git.checkout(branch)
        except GitError as ex:
            raise GitOpsException(f"Error checking out branch '{branch}'") from ex

    def new_branch(self, branch):
        self.__assert_cloned()
        try:
            self.__repo.git.checkout("-b", branch)
        except GitError as ex:
            raise GitOpsException(f"Error creating new branch '{branch}'.") from ex

    def commit(self, git_user, git_email, message):
        self.__assert_cloned()
        try:
            self.__repo.git.add("--all")
            if self.__repo.index.diff("HEAD"):
                self.__repo.config_writer().set_value("user", "name", git_user).release()
                self.__repo.config_writer().set_value("user", "email", git_email).release()
                self.__repo.git.commit("-m", message)
        except GitError as ex:
            raise GitOpsException(f"Error creating commit.") from ex

    def push(self, branch):
        self.__assert_cloned()
        try:
            self.__repo.git.push("--set-upstream", "origin", branch)
        except GitCommandError as ex:
            raise GitOpsException(f"Error pushing branch '{branch}' to origin: {ex.stderr}") from ex
        except GitError as ex:
            raise GitOpsException(f"Error pushing branch '{branch}' to origin.") from ex

    def get_author_from_last_commit(self):
        self.__assert_cloned()
        last_commit = self.__repo.head.commit
        return self.__repo.git.show("-s", "--format=%an <%ae>", last_commit.hexsha)

    def __delete_tmp_dir(self):
        if self.__tmp_dir:
            delete_tmp_dir(self.__tmp_dir)

    def __assert_cloned(self):
        if not self.__repo:
            raise GitOpsException("Repository not cloned yet!")

    def __create_credentials_file(self, username, password):
        file_path = f"{self.__tmp_dir}/credentials.sh"
        with open(file_path, "w+") as text_file:
            text_file.write("#!/bin/sh\n")
            text_file.write(f"echo username={username}\n")
            text_file.write(f"echo password={password}\n")
        os.chmod(file_path, 0o700)
        return file_path
