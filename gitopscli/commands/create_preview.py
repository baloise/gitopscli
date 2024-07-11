import logging
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gitopscli.git_api import GitApiConfig, GitRepo, GitRepoApi, GitRepoApiFactory
from gitopscli.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io_api.yaml_util import YAMLException, update_yaml_file, yaml_file_dump

from .command import Command
from .common import load_gitops_config


class CreatePreviewCommand(Command):
    @dataclass(frozen=True)
    class Args(GitApiConfig):
        git_user: str
        git_email: str

        git_author_name: str | None
        git_author_email: str | None

        organisation: str
        repository_name: str

        git_hash: str
        preview_id: str

    def __init__(self, args: Args) -> None:
        self.__args = args
        self.__deployment_already_up_to_date_callback: Callable[[str], None] = lambda _: None
        self.__deployment_updated_callback: Callable[[str], None] = lambda _: None
        self.__deployment_created_callback: Callable[[str], None] = lambda _: None

    def register_callbacks(
        self,
        deployment_already_up_to_date_callback: Callable[[str], None],
        deployment_updated_callback: Callable[[str], None],
        deployment_created_callback: Callable[[str], None],
    ) -> None:
        self.__deployment_already_up_to_date_callback = deployment_already_up_to_date_callback
        self.__deployment_updated_callback = deployment_updated_callback
        self.__deployment_created_callback = deployment_created_callback

    def execute(self) -> None:
        gitops_config = self.__get_gitops_config()
        self.__create_preview_info_file(gitops_config)

        preview_target_git_repo_api = self.__create_preview_target_git_repo_api(gitops_config)
        with GitRepo(preview_target_git_repo_api) as preview_target_git_repo:
            preview_target_git_repo.clone(gitops_config.preview_target_branch)

            if gitops_config.is_preview_template_equal_target():
                preview_template_repo = preview_target_git_repo
                created_new_preview = self.__create_preview_from_template_if_not_existing(
                    preview_template_repo,
                    preview_target_git_repo,
                    gitops_config,
                )
            else:
                preview_template_git_repo_api = self.__create_preview_template_git_repo_api(gitops_config)
                with GitRepo(preview_template_git_repo_api) as preview_template_repo:
                    preview_template_repo.clone(gitops_config.preview_template_branch)
                    created_new_preview = self.__create_preview_from_template_if_not_existing(
                        preview_template_repo,
                        preview_target_git_repo,
                        gitops_config,
                    )

            any_values_replaced = self.__replace_values(preview_target_git_repo, gitops_config)
            context = GitOpsConfig.Replacement.PreviewContext(
                gitops_config,
                self.__args.preview_id,
                self.__args.git_hash,
            )

            if not created_new_preview and not any_values_replaced:
                self.__deployment_already_up_to_date_callback(gitops_config.get_uptodate_message(context))
                logging.info("The preview is already up-to-date. I'm done here.")
                return

            self.__commit_and_push(
                preview_target_git_repo,
                f"{'Create new' if created_new_preview else 'Update'} preview environment for "
                f"'{gitops_config.application_name}' and git hash '{self.__args.git_hash}'.",
            )

            if created_new_preview:
                self.__deployment_created_callback(gitops_config.get_created_message(context))
            else:
                self.__deployment_updated_callback(gitops_config.get_updated_message(context))

    def __commit_and_push(self, git_repo: GitRepo, message: str) -> None:
        git_repo.commit(
            self.__args.git_user,
            self.__args.git_email,
            self.__args.git_author_name,
            self.__args.git_author_email,
            message,
        )
        git_repo.pull_rebase()
        git_repo.push()

    def __get_gitops_config(self) -> GitOpsConfig:
        return load_gitops_config(self.__args, self.__args.organisation, self.__args.repository_name)

    def __create_preview_template_git_repo_api(self, gitops_config: GitOpsConfig) -> GitRepoApi:
        return GitRepoApiFactory.create(
            self.__args,
            gitops_config.preview_template_organisation,
            gitops_config.preview_template_repository,
        )

    def __create_preview_target_git_repo_api(self, gitops_config: GitOpsConfig) -> GitRepoApi:
        return GitRepoApiFactory.create(
            self.__args,
            gitops_config.preview_target_organisation,
            gitops_config.preview_target_repository,
        )

    def __create_preview_from_template_if_not_existing(
        self,
        template_git_repo: GitRepo,
        target_git_repo: GitRepo,
        gitops_config: GitOpsConfig,
    ) -> bool:
        preview_namespace = gitops_config.get_preview_namespace(self.__args.preview_id)
        full_preview_folder_path = target_git_repo.get_full_file_path(preview_namespace)
        preview_env_already_exist = Path(full_preview_folder_path).is_dir()
        if preview_env_already_exist:
            logging.info("Use existing folder for preview: %s", preview_namespace)
            return False
        logging.info("Create new folder for preview: %s", preview_namespace)
        full_preview_template_folder_path = template_git_repo.get_full_file_path(gitops_config.preview_template_path)
        if not Path(full_preview_template_folder_path).is_dir():
            raise GitOpsException(f"The preview template folder does not exist: {gitops_config.preview_template_path}")
        logging.info("Using the preview template folder: %s", gitops_config.preview_template_path)
        shutil.copytree(full_preview_template_folder_path, full_preview_folder_path)
        return True

    def __replace_values(self, git_repo: GitRepo, gitops_config: GitOpsConfig) -> bool:
        preview_id = self.__args.preview_id
        preview_folder_name = gitops_config.get_preview_namespace(self.__args.preview_id)
        context = GitOpsConfig.Replacement.PreviewContext(gitops_config, preview_id, self.__args.git_hash)
        any_value_replaced = False
        for file, replacements in gitops_config.replacements.items():
            for replacement in replacements:
                replacement_value = replacement.get_value(context)
                value_replaced = self.__update_yaml_file(
                    git_repo,
                    f"{preview_folder_name}/{file}",
                    replacement.path,
                    replacement_value,
                )
                if value_replaced:
                    any_value_replaced = True
                    logging.info(
                        "Replaced property '%s' in '%s' with value: %s",
                        replacement.path,
                        file,
                        replacement_value,
                    )
                else:
                    logging.info("Keep property '%s' in '%s' value: %s", replacement.path, file, replacement_value)
        return any_value_replaced

    def __create_preview_info_file(self, gitops_config: GitOpsConfig) -> None:
        preview_id = self.__args.preview_id
        yaml_file_dump(
            {
                "previewId": preview_id,
                "previewIdHash": gitops_config.create_preview_id_hash(preview_id),
                "routeHost": gitops_config.get_preview_host(preview_id),
                "namespace": gitops_config.get_preview_namespace(preview_id),
            },
            "/tmp/gitopscli-preview-info.yaml",  # noqa: S108
        )

    @staticmethod
    def __update_yaml_file(git_repo: GitRepo, file_path: str, key: str, value: Any) -> bool:
        full_file_path = git_repo.get_full_file_path(file_path)
        try:
            return update_yaml_file(full_file_path, key, value)
        except (FileNotFoundError, IsADirectoryError) as ex:
            raise GitOpsException(f"No such file: {file_path}") from ex
        except YAMLException as ex:
            raise GitOpsException(f"Error loading file: {file_path}") from ex
        except KeyError as ex:
            raise GitOpsException(f"Key '{key}' not found in file: {file_path}") from ex
