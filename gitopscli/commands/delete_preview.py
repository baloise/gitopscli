import hashlib
import logging
import os
import shutil
from typing import Optional

from gitopscli.git import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.gitops_exception import GitOpsException

from .common import load_gitops_config


def delete_preview_command(
    command: str,
    username: Optional[str],
    password: Optional[str],
    git_user: str,
    git_email: str,
    organisation: str,
    repository_name: str,
    git_provider: Optional[str],
    git_provider_url: Optional[str],
    preview_id: str,
    expect_preview_exists: bool,
) -> None:
    assert command == "delete-preview"

    git_api_config = GitApiConfig(username, password, git_provider, git_provider_url,)

    gitops_config = load_gitops_config(git_api_config, organisation, repository_name)

    config_git_repo_api = GitRepoApiFactory.create(
        git_api_config, gitops_config.team_config_org, gitops_config.team_config_repo,
    )
    with GitRepo(config_git_repo_api) as config_git_repo:
        config_git_repo.checkout("master")
        hashed_preview_id = hashlib.sha256(preview_id.encode("utf-8")).hexdigest()[:8]
        preview_folder_name = gitops_config.application_name + "-" + hashed_preview_id + "-preview"
        logging.info("Preview folder name: %s", preview_folder_name)
        preview_folder_full_path = config_git_repo.get_full_file_path(preview_folder_name)
        branch_preview_env_exists = os.path.exists(preview_folder_full_path)

        if expect_preview_exists and not branch_preview_env_exists:
            raise GitOpsException(f"There was no preview with name: {preview_folder_name}")

        if branch_preview_env_exists:
            shutil.rmtree(preview_folder_full_path, ignore_errors=True)
            config_git_repo.commit(
                git_user,
                git_email,
                f"Delete preview environment for '{gitops_config.application_name}' and preview id '{preview_id}'.",
            )
            config_git_repo.push("master")
        else:
            logging.info(
                "No preview environment for '%s' and preview id '%s'. Nothing to do..",
                gitops_config.application_name,
                preview_id,
            )
