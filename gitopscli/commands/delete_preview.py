import hashlib
import logging
import os
import shutil

from gitopscli.git import create_git
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io.gitops_config import GitOpsConfig


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
    expect_preview_exists,
):
    assert command is not None

    with create_git(
        username, password, git_user, git_email, organisation, repository_name, git_provider, git_provider_url,
    ) as apps_git:
        apps_git.checkout("master")
        logging.info("App repo '%s/%s' branch 'master' checkout successful", organisation, repository_name)
        try:
            gitops_config = GitOpsConfig(apps_git.get_full_file_path(".gitops.config.yaml"))
        except FileNotFoundError as ex:
            raise GitOpsException(f"Couldn't find .gitops.config.yaml") from ex
        logging.info("Read .gitops.config.yaml")

    with create_git(
        username,
        password,
        git_user,
        git_email,
        gitops_config.team_config_org,
        gitops_config.team_config_repo,
        git_provider,
        git_provider_url,
    ) as root_git:
        root_git.checkout("master")
        logging.info(
            "Config repo '%s/%s' branch 'master' checkout successful",
            gitops_config.team_config_org,
            gitops_config.team_config_repo,
        )
        hashed_preview_id = hashlib.sha256(preview_id.encode("utf-8")).hexdigest()[:8]
        preview_folder_name = gitops_config.application_name + "-" + hashed_preview_id + "-preview"
        logging.info("Preview folder name: %s", preview_folder_name)
        preview_folder_full_path = root_git.get_full_file_path(preview_folder_name)
        branch_preview_env_exists = os.path.exists(preview_folder_full_path)

        if expect_preview_exists and not branch_preview_env_exists:
            raise GitOpsException(f"There was no preview with name: {preview_folder_name}")

        if branch_preview_env_exists:
            shutil.rmtree(preview_folder_full_path, ignore_errors=True)
            root_git.commit(
                f"Delete preview environment for '{gitops_config.application_name}' and preview id '{preview_id}'."
            )
            root_git.push("master")
            logging.info("Pushed branch 'master'")
        else:
            logging.info(
                "No preview environment for '%s' and preview id '%s'. Nothing to do..",
                gitops_config.application_name,
                preview_id,
            )
