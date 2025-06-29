import logging
from dataclasses import dataclass

from gitopscli.appconfig_api.app_tenant_config import create_app_tenant_config_from_repo
from gitopscli.appconfig_api.root_repo import create_root_repo
from gitopscli.commands.command import Command
from gitopscli.git_api import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io_api.yaml_util import yaml_file_dump


class SyncAppsCommand(Command):
    @dataclass(frozen=True)
    class Args(GitApiConfig):
        git_user: str
        git_email: str

        git_author_name: str | None
        git_author_email: str | None

        organisation: str
        repository_name: str

        root_organisation: str
        root_repository_name: str

    def __init__(self, args: Args) -> None:
        self.__args = args

    def execute(self) -> None:
        _sync_apps_command(self.__args)


def _sync_apps_command(args: SyncAppsCommand.Args) -> None:
    team_config_git_repo_api = GitRepoApiFactory.create(args, args.organisation, args.repository_name)
    root_config_git_repo_api = GitRepoApiFactory.create(args, args.root_organisation, args.root_repository_name)
    with (
        GitRepo(team_config_git_repo_api) as team_config_git_repo,
        GitRepo(root_config_git_repo_api) as root_config_git_repo,
    ):
        __sync_apps(
            team_config_git_repo,
            root_config_git_repo,
            args.git_user,
            args.git_email,
            args.git_author_name,
            args.git_author_email,
        )


def __sync_apps(
    tenant_git_repo: GitRepo,
    root_git_repo: GitRepo,
    git_user: str,
    git_email: str,
    git_author_name: str | None,
    git_author_email: str | None,
) -> None:
    logging.info("Team config repository: %s", tenant_git_repo.get_clone_url())
    logging.info("Root config repository: %s", root_git_repo.get_clone_url())
    root_repo = create_root_repo(root_repo=root_git_repo)
    root_repo_tenant = root_repo.get_tenant_by_repo_url(tenant_git_repo.get_clone_url())
    if root_repo_tenant is None:
        raise GitOpsException("Couldn't find config file for apps repository in root repository's 'apps/' directory")
    tenant_from_repo = create_app_tenant_config_from_repo(tenant_repo=tenant_git_repo)
    logging.info(
        "Found %s app(s) in apps repository: %s",
        len(tenant_from_repo.list_apps().keys()),
        ", ".join(tenant_from_repo.list_apps().keys()),
    )
    root_repo.validate_tenant(tenant_from_repo)
    root_repo_tenant.merge_applications(tenant_from_repo)
    if root_repo_tenant.dirty:
        logging.info("Appling changes to: %s", root_repo_tenant.file_path)
        yaml_file_dump(root_repo_tenant.yaml, root_repo_tenant.file_path)
        logging.info("Commiting and pushing changes to %s", root_git_repo.get_clone_url())
        __commit_and_push(
            tenant_git_repo,
            root_git_repo,
            git_user,
            git_email,
            git_author_name,
            git_author_email,
            root_repo_tenant.file_path,
        )
    else:
        logging.info("No changes applied to %s", root_repo_tenant.file_path)


def __commit_and_push(
    team_config_git_repo: GitRepo,
    root_config_git_repo: GitRepo,
    git_user: str,
    git_email: str,
    git_author_name: str | None,
    git_author_email: str | None,
    app_file_name: str,
) -> None:
    author = team_config_git_repo.get_author_from_last_commit()
    root_config_git_repo.commit(
        git_user,
        git_email,
        git_author_name,
        git_author_email,
        f"{author} updated " + app_file_name,
    )
    root_config_git_repo.pull_rebase()
    root_config_git_repo.push()
