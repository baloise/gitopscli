import os
import sys
from pathlib import Path
from abc import ABC, abstractmethod
from git import Repo


def create_git(username, password, git_user, git_email, organisation, repository_name, git_provider, git_provider_url,
               tmp_dir):
    if git_provider == "bitbucket-server":
        if not git_provider_url:
            print(f"Please provide --git-provider-url for bitbucket-server", file=sys.stderr)
            sys.exit(1)
        from gitopscli.bitbucket_git_util import BitBucketGitUtil
        git = BitBucketGitUtil(
            tmp_dir, git_provider_url, organisation, repository_name, username, password, git_user, git_email
        )
    elif git_provider == "github":
        from gitopscli.github_git_util import GithubGitUtil
        git = GithubGitUtil(tmp_dir, organisation, repository_name, username, password, git_user, git_email)
    else:
        print(f"Git provider '{git_provider}' is not supported.", file=sys.stderr)
        sys.exit(1)
    return git


class AbstractGitUtil(ABC):
    _repo = None

    def __init__(self, tmp_dir, username, password, git_user, git_email):
        self._tmp_dir = tmp_dir
        self._username = username
        self._password = password
        self._git_user = git_user
        self._git_email = git_email

    def get_full_file_path(self, file_path):
        return Path(os.path.join(self._repo.working_dir, file_path))

    def checkout(self, branch):
        git_options = []
        if self._username is not None and self._password is not None:
            credentials_file = self.create_credentials_file(self._tmp_dir, self._username, self._password)
            git_options.append(f"--config credential.helper={credentials_file}")
        self._repo = Repo.clone_from(
            url=self.get_clone_url(), to_path=f"{self._tmp_dir}/{branch}", multi_options=git_options
        )
        self._repo.create_head(branch).checkout()

    def commit(self, message):
        self._repo.git.add(u=True)
        if self._repo.index.diff("HEAD"):
            self._repo.config_writer().set_value("user", "name", self._git_user).release()
            self._repo.config_writer().set_value("user", "email", self._git_email).release()
            self._repo.git.commit("-m", message)

    def push(self, branch):
        self._repo.git.push("origin", branch)

    @staticmethod
    def create_credentials_file(directory, username, password):
        file_path = f"{directory}/credentials.sh"
        with open(file_path, "w+") as text_file:
            text_file.write("#!/bin/bash\n")
            text_file.write(f"echo username={username}\n")
            text_file.write(f"echo password={password}\n")
        os.chmod(file_path, 0o700)
        return file_path

    @abstractmethod
    def get_clone_url(self):
        pass

    @abstractmethod
    def create_pull_request(self, from_branch, to_branch, title, description):
        pass

    @abstractmethod
    def get_pull_request_url(self, pull_request):
        pass

    @abstractmethod
    def merge_pull_request(self, pull_request):
        pass

    @abstractmethod
    def delete_branch(self, branch):
        pass
