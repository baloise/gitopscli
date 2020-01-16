import os
import shutil
from git import Repo
from pathlib import Path


class GitUtil:
    def __init__(self, repo, branch_name):
        tmp_dir = "/tmp/gitopscli"
        shutil.rmtree(tmp_dir, ignore_errors=True)
        os.makedirs(tmp_dir)

        self._repo = Repo.clone_from(repo, tmp_dir)
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
