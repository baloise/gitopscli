import hashlib
import logging
import os
import uuid
import shutil

from gitopscli.git.create_git import create_git
from gitopscli.io.gitops_config import GitOpsConfig
from gitopscli.io.tmp_dir import create_tmp_dir, delete_tmp_dir
from gitopscli.gitops_exception import GitOpsException


def delete_preview_command(
    command,
    username,
    password,
    git_user,
    git_email,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
    preview_id,
):

    apps_tmp_dir = create_tmp_dir()
    root_tmp_dir = create_tmp_dir()

    try:
        apps_git = create_git(
            username,
            password,
            git_user,
            git_email,
            organisation,
            repository_name,
            git_provider,
            git_provider_url,
            apps_tmp_dir,
        )

        apps_git.checkout("master")
        logging.info("App repo branch master checkout successful")
        try:
            gitops_config = GitOpsConfig(apps_git.get_full_file_path(".gitops.config.yaml"))
        except FileNotFoundError as ex:
            raise GitOpsException(f"Couldn't find .gitops.config.yaml") from ex
        logging.info("Read GitOpsConfig: %s", gitops_config)

        root_git = create_git(
            username,
            password,
            git_user,
            git_email,
            gitops_config.team_config_org,
            gitops_config.team_config_repo,
            git_provider,
            git_provider_url,
            root_tmp_dir,
        )
        root_git.checkout("master")
        logging.info("Config repo branch master checkout successful")
        config_branch = "master"
        hashed_preview_id = hashlib.sha256(preview_id.encode("utf-8")).hexdigest()[:8]
        preview_folder_name = gitops_config.application_name + "-" + hashed_preview_id + "-preview"
        logging.info("Preview folder name: %s", preview_folder_name)
        branch_preview_env_exists = os.path.exists(root_git.get_full_file_path(preview_folder_name))
        logging.info("Is preview env already existing for branch? %s", branch_preview_env_exists)
        if branch_preview_env_exists:
            shutil.rmtree(root_git.get_full_file_path(preview_folder_name), ignore_errors=True)
        else:
            raise GitOpsException(f"There was no preview with name: {preview_folder_name}")
        root_git.commit(
            f"Delete preview environment for '{gitops_config.application_name}' and preview id '{preview_id}'."
        )
        root_git.push(config_branch)
        logging.info("Pushed branch %s", config_branch)

    finally:
        delete_tmp_dir(apps_tmp_dir)
        delete_tmp_dir(root_tmp_dir)


def __create_tmp_dir():
    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(tmp_dir)
    logging.info("Created directory %s", tmp_dir)
    return tmp_dir
