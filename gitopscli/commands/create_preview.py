import hashlib
import logging
import os
import shutil
from typing import Any, Callable, Dict, Optional, NamedTuple

from gitopscli.git import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.io.yaml_util import update_yaml_file
from gitopscli.gitops_exception import GitOpsException
from .common import load_gitops_config
from .command import Command


class CreatePreviewCommand(Command):
    class Args(NamedTuple):
        git_provider: Optional[str]
        git_provider_url: Optional[str]

        username: str
        password: str

        git_user: str
        git_email: str

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

    def execute(self,) -> None:
        _create_preview_command(
            self.__args,
            self.__deployment_already_up_to_date_callback,
            self.__deployment_updated_callback,
            self.__deployment_created_callback,
        )


def _create_preview_command(
    args: CreatePreviewCommand.Args,
    deployment_already_up_to_date_callback: Callable[[str], None],
    deployment_updated_callback: Callable[[str], None],
    deployment_created_callback: Callable[[str], None],
) -> None:
    git_api_config = GitApiConfig(args.username, args.password, args.git_provider, args.git_provider_url,)
    gitops_config = load_gitops_config(git_api_config, args.organisation, args.repository_name)

    config_git_repo_api = GitRepoApiFactory.create(
        git_api_config, gitops_config.team_config_org, gitops_config.team_config_repo,
    )
    with GitRepo(config_git_repo_api) as config_git_repo:
        config_git_repo.checkout("master")

        preview_template_folder_name = ".preview-templates/" + gitops_config.application_name
        if not os.path.isdir(config_git_repo.get_full_file_path(preview_template_folder_name)):
            raise GitOpsException(f"The preview template folder does not exist: {preview_template_folder_name}")
        logging.info("Using the preview template folder: %s", preview_template_folder_name)

        hashed_preview_id = hashlib.sha256(args.preview_id.encode("utf-8")).hexdigest()[:8]
        new_preview_folder_name = gitops_config.application_name + "-" + hashed_preview_id + "-preview"
        logging.info("New folder for preview: %s", new_preview_folder_name)
        preview_env_already_exist = os.path.isdir(config_git_repo.get_full_file_path(new_preview_folder_name))
        logging.info("Is preview env already existing? %s", preview_env_already_exist)
        if not preview_env_already_exist:
            __create_new_preview_env(
                new_preview_folder_name, preview_template_folder_name, config_git_repo,
            )

        logging.info("Using image tag from git hash: %s", args.git_hash)
        route_host = gitops_config.route_host.replace("{SHA256_8CHAR_BRANCH_HASH}", hashed_preview_id)
        value_replaced = False
        for replacement in gitops_config.replacements:
            value_replaced = value_replaced | __replace_value(
                args.git_hash, route_host, new_preview_folder_name, replacement, config_git_repo,
            )
        if not value_replaced:
            logging.info("The image tag %s has already been deployed. Doing nothing.", args.git_hash)
            deployment_already_up_to_date_callback(route_host)
            return

        commit_msg_verb = "Update" if preview_env_already_exist else "Create new"
        config_git_repo.commit(
            args.git_user,
            args.git_email,
            f"{commit_msg_verb} preview environment for '{gitops_config.application_name}' "
            f"and git hash '{args.git_hash}'.",
        )
        config_git_repo.push("master")

        if preview_env_already_exist:
            deployment_updated_callback(route_host)
        else:
            deployment_created_callback(route_host)


def __replace_value(
    new_image_tag: str, route_host: str, new_preview_folder_name: str, replacement: Dict[str, Any], root_git: GitRepo,
) -> bool:
    replacement_value = None
    logging.info("Replacement: %s", replacement)
    replacement_path = replacement["path"]
    replacement_variable = replacement["variable"]
    if replacement_variable == "GIT_COMMIT":
        replacement_value = new_image_tag
    elif replacement_variable == "ROUTE_HOST":
        replacement_value = route_host
    else:
        logging.info("Unknown replacement variable: %s", replacement_variable)
    value_replaced = False
    try:
        value_replaced = update_yaml_file(
            root_git.get_full_file_path(new_preview_folder_name + "/values.yaml"), replacement_path, replacement_value,
        )
    except KeyError as ex:
        raise GitOpsException(f"Key '{replacement_path}' not found in '{new_preview_folder_name}/values.yaml'") from ex
    logging.info("Replacing property %s with value: %s", replacement_path, replacement_value)
    return value_replaced


def __create_new_preview_env(
    new_preview_folder_name: str, preview_template_folder_name: str, config_git_repo: GitRepo,
) -> None:
    shutil.copytree(
        config_git_repo.get_full_file_path(preview_template_folder_name),
        config_git_repo.get_full_file_path(new_preview_folder_name),
    )
    chart_file_path = new_preview_folder_name + "/Chart.yaml"
    logging.info("Looking for Chart.yaml at: %s", chart_file_path)
    if config_git_repo.get_full_file_path(chart_file_path):
        try:
            update_yaml_file(config_git_repo.get_full_file_path(chart_file_path), "name", new_preview_folder_name)
        except KeyError as ex:
            raise GitOpsException(f"Key 'name' not found in '{chart_file_path}'") from ex
