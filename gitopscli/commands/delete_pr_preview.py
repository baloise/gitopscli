import hashlib
import logging
import os
import uuid

from gitopscli.commands import delete_preview_command
from gitopscli.git.create_git import create_git
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io.gitops_config import GitOpsConfig
from gitopscli.io.tmp_dir import create_tmp_dir, delete_tmp_dir


def delete_pr_preview_command(
    command,
    branch,
    username,
    password,
    git_user,
    git_email,
    organisation,
    repository_name,
    git_provider,
    git_provider_url,
):
    assert command == "delete-pr-preview"

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

        apps_git.checkout(branch)
        preview_id = hashlib.sha256(branch.encode("utf-8")).hexdigest()[:8]
        logging.info("App repo branch %s checkout successful", branch)
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

        delete_preview_command(
            command,
            username,
            password,
            git_user,
            git_email,
            organisation,
            repository_name,
            git_provider,
            git_provider_url,
            preview_id
        )

    finally:
        delete_tmp_dir(apps_tmp_dir)
        delete_tmp_dir(root_tmp_dir)

def __create_tmp_dir():
    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(tmp_dir)
    logging.info("Created directory %s", tmp_dir)
    return tmp_dir
