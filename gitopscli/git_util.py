import os
import shutil
from git import Repo
from pathlib import Path


class GitUtil:
    def __init__(self, repo, branch_name, tmp_dir, username=None, password=None):
        shutil.rmtree(tmp_dir, ignore_errors=True)
        os.makedirs(tmp_dir)
        git_options = []
        if username is not None and password is not None:
            credentials_file = self.create_credentials_file(tmp_dir, username, password)
            git_options.append(f"--config credential.helper={credentials_file.name}")
        self._repo = Repo.clone_from(url=repo, to_path=tmp_dir + "/" + branch_name, multi_options=git_options)
        self._repo.create_head(branch_name).checkout()

        self._branch_name = branch_name

    def get_full_file_path(self, file_path):
        return Path(os.path.join(self._repo.working_dir, file_path))

    def commit(self, message):
        self._repo.git.add(u=True)
        if self._repo.index.diff("HEAD"):
            self._repo.config_writer().set_value("user", "name", "gitopscli").release()
            self._repo.config_writer().set_value("user", "email", "gitopscli@baloise.com").release()
            self._repo.git.commit("-m", message)

    def push(self):
        self._repo.git.push("origin", self._branch_name)

    def create_credentials_file(self, tmp_dir, username, password):
        credentials_file = f"""#!/bin/bash
echo username={username}
echo password={password}
    """
        text_file = open(f"{tmp_dir}/credentials.sh", "w+")
        text_file.write(credentials_file)
        text_file.close()
        os.chmod(text_file.name, 0o700)
        return text_file
