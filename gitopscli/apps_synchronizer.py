import os
import uuid

from gitopscli.abstract_git_util import create_git


class AppsSynchronizer:

    def sync_apps(self, apps_git, root_git):
        apps_git.checkout("master")
        full_file_path = apps_git.get_full_file_path(".")
        # WIP
        print(full_file_path)