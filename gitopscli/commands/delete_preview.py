import hashlib
import logging
import os
import shutil

from typing import Optional, NamedTuple
from gitopscli.git import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.gitops_exception import GitOpsException

from .common import load_gitops_config


class DeletePreviewArgs(NamedTuple):
    git_provider: Optional[str]
    git_provider_url: Optional[str]

    username: str
    password: str

    git_user: str
    git_email: str

    organisation: str
    repository_name: str

    preview_id: str
    expect_preview_exists: bool


def delete_preview_command(args: DeletePreviewArgs) -> None:
    git_api_config = GitApiConfig(args.username, args.password, args.git_provider, args.git_provider_url,)
    gitops_config = load_gitops_config(git_api_config, args.organisation, args.repository_name)

    config_git_repo_api = GitRepoApiFactory.create(
        git_api_config, gitops_config.team_config_org, gitops_config.team_config_repo,
    )
    with GitRepo(config_git_repo_api) as config_git_repo:
        config_git_repo.checkout("master")
        hashed_preview_id = hashlib.sha256(args.preview_id.encode("utf-8")).hexdigest()[:8]
        preview_folder_name = gitops_config.application_name + "-" + hashed_preview_id + "-preview"
        logging.info("Preview folder name: %s", preview_folder_name)
        preview_folder_full_path = config_git_repo.get_full_file_path(preview_folder_name)
        branch_preview_env_exists = os.path.exists(preview_folder_full_path)

        if args.expect_preview_exists and not branch_preview_env_exists:
            raise GitOpsException(f"There was no preview with name: {preview_folder_name}")

        if branch_preview_env_exists:
            shutil.rmtree(preview_folder_full_path, ignore_errors=True)
            config_git_repo.commit(
                args.git_user,
                args.git_email,
                f"Delete preview environment for '{gitops_config.application_name}' "
                f"and preview id '{args.preview_id}'.",
            )
            config_git_repo.push("master")
        else:
            logging.info(
                "No preview environment for '%s' and preview id '%s'. Nothing to do..",
                gitops_config.application_name,
                args.preview_id,
            )
