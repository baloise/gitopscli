import logging
import os
from dataclasses import dataclass, field
from typing import Any

from gitopscli.git_api import GitRepo
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io_api.yaml_util import yaml_file_load, yaml_load


@dataclass
class AppTenantConfig:
    yaml: dict[str, dict[str, Any]]
    tenant_config: dict[str, dict[str, Any]] = field(default_factory=dict)
    repo_url: str = ""
    file_path: str = ""
    dirty: bool = False

    def __post_init__(self) -> None:
        self.tenant_config = self.yaml.get("config", self.yaml)
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
                elif (
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
            if desired_app_name not in self.list_apps():
                logging.info("Adding %s in %s applications", desired_app_name, self.file_path)
                self.tenant_config["applications"][desired_app_name] = desired_app_value
                self.__set_dirty()

    def __delete_removed_applications(self, desired_apps: dict[str, Any]) -> None:
        for current_app in self.list_apps():
            if current_app not in desired_apps:
                logging.info("Removing %s from %s applications", current_app, self.file_path)
                del self.tenant_config["applications"][current_app]
                self.__set_dirty()

    def __set_dirty(self) -> None:
        self.dirty = True


def __generate_config_from_tenant_repo(
    tenant_repo: GitRepo,
) -> Any:  # TODO: supposed to be ruamel object than Any # noqa: FIX002
    tenant_app_dirs = __get_all_tenant_applications_dirs(tenant_repo)
    tenant_config_template = f"""
    config:
        repository: {tenant_repo.get_clone_url()}
        applications: {{}}
    """
    yaml = yaml_load(tenant_config_template)
    for app_dir in tenant_app_dirs:
        tenant_application_template = f"""
        {app_dir}: {{}}
        """
        tenant_applications_yaml = yaml_load(tenant_application_template)
        # dict path hardcoded as object generated will always be in v2 or later
        yaml["config"]["applications"].update(tenant_applications_yaml)
        custom_app_config = __get_custom_config(app_dir, tenant_repo)
        if custom_app_config:
            yaml["config"]["applications"][app_dir]["customAppConfig"] = custom_app_config
    return yaml


def __get_all_tenant_applications_dirs(tenant_repo: GitRepo) -> set[str]:
    repo_dir = tenant_repo.get_full_file_path(".")
    return {
        name
        for name in os.listdir(repo_dir)
        if os.path.isdir(os.path.join(repo_dir, name)) and not name.startswith(".")
    }


def __get_custom_config(appname: str, tenant_config_git_repo: GitRepo) -> Any:
    custom_config_path = tenant_config_git_repo.get_full_file_path(f"{appname}/.config.yaml")
    if os.path.exists(custom_config_path):
        return yaml_file_load(custom_config_path)
    return {}


def create_app_tenant_config_from_repo(
    tenant_repo: GitRepo,
) -> "AppTenantConfig":
    tenant_repo.clone()
    tenant_config_yaml = __generate_config_from_tenant_repo(tenant_repo)
    return AppTenantConfig(yaml=tenant_config_yaml)
