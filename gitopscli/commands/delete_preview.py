import logging
import os
import shutil
from dataclasses import dataclass
from gitopscli.git import GitApiConfig, GitRepo, GitRepoApiFactory, GitRepoApi
from gitopscli.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException
from .common import load_gitops_config
from .command import Command


class DeletePreviewCommand(Command):
    @dataclass(frozen=True)
    class Args(GitApiConfig):
        git_user: str
        git_email: str

        organisation: str
        repository_name: str

        preview_id: str
        expect_preview_exists: bool

    def __init__(self, args: Args) -> None:
        self.__args = args

    def execute(self) -> None:
        gitops_config = self.__get_gitops_config()
        preview_id = self.__args.preview_id

        team_config_git_repo_api = self.__create_team_config_git_repo_api(gitops_config)
        with GitRepo(team_config_git_repo_api) as team_config_git_repo:
            team_config_git_repo.checkout("master")

            preview_namespace = gitops_config.get_preview_namespace(preview_id)
            logging.info("Preview folder name: %s", preview_namespace)

            preview_folder_exists = self.__delete_folder_if_exists(team_config_git_repo, preview_namespace)
            if not preview_folder_exists:
                if self.__args.expect_preview_exists:
                    raise GitOpsException(f"There was no preview with name: {preview_namespace}")
                logging.info(
                    "No preview environment for '%s' and preview id '%s'. I'm done here.",
                    gitops_config.application_name,
                    preview_id,
                )
                return

            self.__commit_and_push(
                team_config_git_repo,
                f"Delete preview environment for '{gitops_config.application_name}' and preview id '{preview_id}'.",
            )

    def __get_gitops_config(self) -> GitOpsConfig:
        return load_gitops_config(self.__args, self.__args.organisation, self.__args.repository_name)

    def __create_team_config_git_repo_api(self, gitops_config: GitOpsConfig) -> GitRepoApi:
        return GitRepoApiFactory.create(self.__args, gitops_config.team_config_org, gitops_config.team_config_repo)

    def __commit_and_push(self, git_repo: GitRepo, message: str) -> None:
        git_repo.commit(self.__args.git_user, self.__args.git_email, message)
        git_repo.push("master")

    @staticmethod
    def __delete_folder_if_exists(git_repo: GitRepo, folder_name: str) -> bool:
        folder_full_path = git_repo.get_full_file_path(folder_name)
        if not os.path.exists(folder_full_path):
            return False
        shutil.rmtree(folder_full_path, ignore_errors=True)
        return True
