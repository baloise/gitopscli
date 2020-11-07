import logging
import os
import uuid

from gitopscli.commands import delete_preview_command
from gitopscli.git.create_git import create_git
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io.gitops_config import GitOpsConfig


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
    expect_preview_exists,
):
    assert command == "delete-pr-preview"

    with create_git(
        username, password, git_user, git_email, organisation, repository_name, git_provider, git_provider_url,
    ) as apps_git:

        app_master_branch_name = "master"
        apps_git.checkout(app_master_branch_name)
        logging.info("App repo branch %s checkout successful", app_master_branch_name)
        try:
            gitops_config = GitOpsConfig(apps_git.get_full_file_path(".gitops.config.yaml"))
        except FileNotFoundError as ex:
            raise GitOpsException(f"Couldn't find .gitops.config.yaml") from ex
        logging.info("Read GitOpsConfig: %s", gitops_config)

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
            branch,
            expect_preview_exists,
        )


def __create_tmp_dir():
    tmp_dir = f"/tmp/gitopscli/{uuid.uuid4()}"
    os.makedirs(tmp_dir)
    logging.info("Created directory %s", tmp_dir)
    return tmp_dir
