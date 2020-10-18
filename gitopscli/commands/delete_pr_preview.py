import logging
import os
import uuid

from gitopscli.commands import delete_preview_command
from gitopscli.git import create_git, GitConfig
from .common import load_gitops_config


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

    git_config = GitConfig(
        username=username,
        password=password,
        git_user=git_user,
        git_email=git_email,
        git_provider=git_provider,
        git_provider_url=git_provider_url,
    )

    gitops_config = load_gitops_config(git_config, organisation, repository_name)

    with create_git(git_config, gitops_config.team_config_org, gitops_config.team_config_repo) as root_git:
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
