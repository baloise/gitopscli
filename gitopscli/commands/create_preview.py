import hashlib
import logging
import os
import shutil

from gitopscli.git import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.io.yaml_util import update_yaml_file
from gitopscli.gitops_exception import GitOpsException
from .common import load_gitops_config


def create_preview_command(
    command,
    username,
    password,
    git_user,
    git_email,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
    git_hash,
    preview_id,
    deployment_already_up_to_date_callback=lambda: None,
    deployment_exists_callback=lambda: None,
    deployment_new_callback=lambda: None,
):
    assert command == "create-preview"

    git_api_config = GitApiConfig(
        username=username, password=password, git_provider=git_provider, git_provider_url=git_provider_url,
    )

    gitops_config = load_gitops_config(git_api_config, organisation, repository_name)

    config_git_repo_api = GitRepoApiFactory.create(
        config=git_api_config,
        organisation=gitops_config.team_config_org,
        repository_name=gitops_config.team_config_repo,
    )
    with GitRepo(config_git_repo_api) as config_git_repo:
        config_git_repo.checkout("master")
        logging.info("Config repo branch master checkout successful")

        preview_template_folder_name = ".preview-templates/" + gitops_config.application_name
        if not os.path.isdir(config_git_repo.get_full_file_path(preview_template_folder_name)):
            raise GitOpsException(f"The preview template folder does not exist: {preview_template_folder_name}")
        logging.info("Using the preview template folder: %s", preview_template_folder_name)

        hashed_preview_id = hashlib.sha256(preview_id.encode("utf-8")).hexdigest()[:8]
        new_preview_folder_name = gitops_config.application_name + "-" + hashed_preview_id + "-preview"
        logging.info("New folder for preview: %s", new_preview_folder_name)
        preview_env_already_exist = os.path.isdir(config_git_repo.get_full_file_path(new_preview_folder_name))
        logging.info("Is preview env already existing? %s", preview_env_already_exist)
        if not preview_env_already_exist:
            __create_new_preview_env(
                new_preview_folder_name, preview_template_folder_name, config_git_repo,
            )

        logging.info("Using image tag from git hash: %s", git_hash)
        route_host = None
        value_replaced = False
        for replacement in gitops_config.replacements:
            route_host, value_replaced = __replace_value(
                gitops_config,
                git_hash,
                new_preview_folder_name,
                replacement,
                config_git_repo,
                route_host,
                hashed_preview_id,
                value_replaced,
            )
        if not value_replaced:
            logging.info("The image tag %s has already been deployed. Doing nothing.", git_hash)
            deployment_already_up_to_date_callback(route_host)
            return

        commit_msg_verb = "Update" if preview_env_already_exist else "Create new"
        config_git_repo.commit(
            git_user,
            git_email,
            f"{commit_msg_verb} preview environment for '{gitops_config.application_name}' and git hash '{git_hash}'.",
        )
        config_git_repo.push("master")
        logging.info("Pushed branch master")

        if preview_env_already_exist:
            deployment_exists_callback(route_host)
        else:
            deployment_new_callback(route_host)


def __replace_value(
    gitops_config,
    new_image_tag,
    new_preview_folder_name,
    replacement,
    root_git,
    route_host,
    hashed_preview_id,
    value_replaced,
):
    replacement_value = None
    logging.info("Replacement: %s", replacement)
    replacement_path = replacement["path"]
    replacement_variable = replacement["variable"]
    if replacement_variable == "GIT_COMMIT":
        replacement_value = new_image_tag
    elif replacement_variable == "ROUTE_HOST":
        route_host = gitops_config.route_host.replace("{SHA256_8CHAR_BRANCH_HASH}", hashed_preview_id)
        logging.info("Created route host: %s", route_host)
        replacement_value = route_host
    else:
        logging.info("Unknown replacement variable: %s", replacement_variable)
    try:
        value_replaced = value_replaced | update_yaml_file(
            root_git.get_full_file_path(new_preview_folder_name + "/values.yaml"), replacement_path, replacement_value,
        )
    except KeyError as ex:
        raise GitOpsException(f"Key '{replacement_path}' not found in '{new_preview_folder_name}/values.yaml'") from ex
    logging.info("Replacing property %s with value: %s", replacement_path, replacement_value)
    return route_host, value_replaced


def __create_new_preview_env(
    new_preview_folder_name, preview_template_folder_name, config_git_repo: GitRepo,
):
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
