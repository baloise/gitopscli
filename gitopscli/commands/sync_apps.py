import logging
import os
from typing import Any, Optional, List
from dataclasses import dataclass, field
from gitopscli.git_api import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io_api.yaml_util import yaml_file_load, yaml_load, yaml_file_dump
from .command import Command


class TenantAppTenantConfigFactory:
    def __generate_config_from_tenant_repo(
        self, tenant_repo: GitRepo
    ) -> Any:  # TODO: supposed to be ruamel object than Any  pylint: disable=fixme
        tenant_app_dirs = self.__get_all_tenant_applications_dirs(tenant_repo)
        tenant_config_template = """
        config: 
            repository: {}
            applications: {{}}
        """.format(
            tenant_repo.get_clone_url()
        )
        yaml = yaml_load(tenant_config_template)
        for app_dir in tenant_app_dirs:
            tenant_application_template = """
            {}: {{}}
            """.format(
                app_dir
            )
            tenant_applications_yaml = yaml_load(tenant_application_template)
            # dict path hardcoded as object generated will always be in v2 or later
            yaml["config"]["applications"].update(tenant_applications_yaml)
            custom_app_config = self.__get_custom_config(app_dir, tenant_repo)
            if custom_app_config:
                yaml["config"]["applications"][app_dir]["customAppConfig"] = custom_app_config
        return yaml

    @staticmethod
    def __get_all_tenant_applications_dirs(tenant_repo: GitRepo) -> set[str]:
        repo_dir = tenant_repo.get_full_file_path(".")
        applist = {
            name
            for name in os.listdir(repo_dir)
            if os.path.isdir(os.path.join(repo_dir, name)) and not name.startswith(".")
        }
        return applist

    @staticmethod
    def __get_custom_config(appname: str, tenant_config_git_repo: GitRepo) -> Any:
        custom_config_path = tenant_config_git_repo.get_full_file_path(f"{appname}/.config.yaml")
        if os.path.exists(custom_config_path):
            custom_config_content = yaml_file_load(custom_config_path)
            return custom_config_content
        return dict()

    def create(
        self,
        tenant_repo: GitRepo,
    ) -> "AppTenantConfig":
        tenant_repo.clone()
        tenant_config_yaml = self.__generate_config_from_tenant_repo(tenant_repo)
        return AppTenantConfig(yaml=tenant_config_yaml)


@dataclass
class AppTenantConfig:
    yaml: dict[str, dict[str, Any]]
    tenant_config: dict[str, dict[str, Any]] = field(default_factory=dict)
    repo_url: str = ""
    file_path: str = ""
    dirty: bool = False

    def __post_init__(self) -> None:
        if "config" in self.yaml:
            self.tenant_config = self.yaml["config"]
        else:
            self.tenant_config = self.yaml
        if "repository" not in self.tenant_config:
            raise GitOpsException("Cannot find key 'repository' in " + self.file_path)
        self.repo_url = str(self.tenant_config["repository"])

    def list_apps(self) -> dict[str, dict[str, Any]]:
        return dict(self.tenant_config["applications"])

    def merge_applications(self, desired_tenant_config: "AppTenantConfig") -> None:
        desired_apps = desired_tenant_config.list_apps()
        self.__delete_removed_applications(desired_apps)
        self.__add_new_applications(desired_apps)
        self.__update_custom_app_config(desired_apps)

    def __update_custom_app_config(self, desired_apps: dict[str, dict[str, Any]]) -> None:
        for desired_app_name, desired_app_value in desired_apps.items():
            if desired_app_name in self.list_apps():
                existing_application_value = self.list_apps()[desired_app_name]
                if "customAppConfig" not in desired_app_value:
                    if existing_application_value and "customAppConfig" in existing_application_value:
                        logging.info(
                            "Removing customAppConfig in for %s in %s applications",
                            existing_application_value,
                            self.file_path,
                        )
                        del existing_application_value["customAppConfig"]
                        self.__set_dirty()
                else:
                    if (
                        "customAppConfig" not in existing_application_value
                        or existing_application_value["customAppConfig"] != desired_app_value["customAppConfig"]
                    ):
                        logging.info(
                            "Updating customAppConfig in for %s in %s applications",
                            existing_application_value,
                            self.file_path,
                        )
                        existing_application_value["customAppConfig"] = desired_app_value["customAppConfig"]
                        self.__set_dirty()

    def __add_new_applications(self, desired_apps: dict[str, Any]) -> None:
        for desired_app_name, desired_app_value in desired_apps.items():
            if desired_app_name not in self.list_apps().keys():
                logging.info("Adding % in %s applications", desired_app_name, self.file_path)
                self.tenant_config["applications"][desired_app_name] = desired_app_value
                self.__set_dirty()

    def __delete_removed_applications(self, desired_apps: dict[str, Any]) -> None:
        for current_app in self.list_apps().keys():
            if current_app not in desired_apps.keys():
                logging.info("Removing % from %s applications", current_app, self.file_path)
                del self.tenant_config["applications"][current_app]
                self.__set_dirty()

    def __set_dirty(self) -> None:
        self.dirty = True


class RootRepoFactory:
    @staticmethod
    def __load_tenants_from_bootstrap_values(root_repo: GitRepo) -> dict[str, AppTenantConfig]:
        boostrap_tenant_list = RootRepoFactory.__get_bootstrap_tenant_list(root_repo)
        tenants = dict()
        for bootstrap_tenant in boostrap_tenant_list:
            try:
                tenant_name = bootstrap_tenant["name"]
                absolute_tenant_file_path = root_repo.get_full_file_path("apps/" + tenant_name + ".yaml")
                yaml = yaml_file_load(absolute_tenant_file_path)
                tenants[tenant_name] = AppTenantConfig(
                    yaml=yaml,
                    file_path=absolute_tenant_file_path,
                )
            except FileNotFoundError as ex:
                raise GitOpsException(f"File '{absolute_tenant_file_path}' not found in root repository.") from ex
        return tenants

    @staticmethod
    def __get_bootstrap_tenant_list(root_repo: GitRepo) -> List[Any]:
        root_repo.clone()
        try:
            boostrap_values_path = root_repo.get_full_file_path("bootstrap/values.yaml")
            bootstrap_yaml = yaml_file_load(boostrap_values_path)
        except FileNotFoundError as ex:
            raise GitOpsException("File 'bootstrap/values.yaml' not found in root repository.") from ex
        bootstrap_tenants = []
        if "bootstrap" in bootstrap_yaml:
            bootstrap_tenants = list(bootstrap_yaml["bootstrap"])
        if "config" in bootstrap_yaml and "bootstrap" in bootstrap_yaml["config"]:
            bootstrap_tenants = list(bootstrap_yaml["config"]["bootstrap"])
        RootRepoFactory.validate_bootstrap_tenants(bootstrap_tenants)
        return bootstrap_tenants

    @staticmethod
    def validate_bootstrap_tenants(bootstrap_entries: Optional[List[Any]]) -> None:
        if not bootstrap_entries:
            raise GitOpsException("Cannot find key 'bootstrap' or 'config.bootstrap' in 'bootstrap/values.yaml'")
        for bootstrap_entry in bootstrap_entries:
            if "name" not in bootstrap_entry:
                raise GitOpsException("Every bootstrap entry must have a 'name' property.")

    def create(self, root_repo: GitRepo) -> "RootRepo":
        root_repo_tenants = self.__load_tenants_from_bootstrap_values(root_repo)
        return RootRepo(root_repo_tenants)


@dataclass
class RootRepo:
    tenants: dict[str, AppTenantConfig]

    def list_tenants(self) -> list[str]:
        return list(self.tenants.keys())

    def get_tenant_by_repo_url(self, repo_url: str) -> Optional[AppTenantConfig]:
        for tenant in self.tenants.values():
            if tenant.repo_url == repo_url:
                return tenant
        return None

    def get_all_applications(self) -> list[str]:
        apps: list[str] = list()
        for tenant in self.tenants.values():
            apps.extend(tenant.list_apps().keys())
        return apps

    def validate_tenant(self, tenant_config: AppTenantConfig) -> None:
        apps_from_other_tenants: list[str] = list()
        for tenant in self.tenants.values():
            if tenant.repo_url != tenant_config.repo_url:
                apps_from_other_tenants.extend(tenant.list_apps().keys())
        for app_name in tenant_config.list_apps().keys():
            if app_name in apps_from_other_tenants:
                raise GitOpsException(f"Application '{app_name}' already exists in a different repository")


class SyncAppsCommand(Command):
    @dataclass(frozen=True)
    class Args(GitApiConfig):
        git_user: str
        git_email: str

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
    with GitRepo(team_config_git_repo_api) as team_config_git_repo:
        with GitRepo(root_config_git_repo_api) as root_config_git_repo:
            __sync_apps(team_config_git_repo, root_config_git_repo, args.git_user, args.git_email)


# TODO: BETTER NAMES FOR STUFF HERE pylint: disable=fixme
def __sync_apps(tenant_git_repo: GitRepo, root_git_repo: GitRepo, git_user: str, git_email: str) -> None:
    logging.info("Team config repository: %s", tenant_git_repo.get_clone_url())
    logging.info("Root config repository: %s", root_git_repo.get_clone_url())
    root_repo = RootRepoFactory().create(root_repo=root_git_repo)
    root_repo_tenant = root_repo.get_tenant_by_repo_url(tenant_git_repo.get_clone_url())
    if root_repo_tenant is None:
        raise GitOpsException("Couldn't find config file for apps repository in root repository's 'apps/' directory")
    tenant_from_repo = TenantAppTenantConfigFactory().create(tenant_repo=tenant_git_repo)
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
        __commit_and_push(tenant_git_repo, root_git_repo, git_user, git_email, root_repo_tenant.file_path)
    else:
        logging.info("No changes applied to %s", root_repo_tenant.file_path)


def __commit_and_push(
    team_config_git_repo: GitRepo, root_config_git_repo: GitRepo, git_user: str, git_email: str, app_file_name: str
) -> None:
    author = team_config_git_repo.get_author_from_last_commit()
    root_config_git_repo.commit(git_user, git_email, f"{author} updated " + app_file_name)
    root_config_git_repo.push()
