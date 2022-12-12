from dataclasses import dataclass
from typing import List, Any, Optional

from gitopscli.git_api import GitRepo
from gitopscli.io_api.yaml_util import yaml_file_load

from gitopscli.appconfig_api.app_tenant_config import AppTenantConfig
from gitopscli.gitops_exception import GitOpsException


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


def __load_tenants_from_bootstrap_values(root_repo: GitRepo) -> dict[str, AppTenantConfig]:
    boostrap_tenant_list = __get_bootstrap_tenant_list(root_repo)
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
    __validate_bootstrap_tenants(bootstrap_tenants)
    return bootstrap_tenants


def __validate_bootstrap_tenants(bootstrap_entries: Optional[List[Any]]) -> None:
    if not bootstrap_entries:
        raise GitOpsException("Cannot find key 'bootstrap' or 'config.bootstrap' in 'bootstrap/values.yaml'")
    for bootstrap_entry in bootstrap_entries:
        if "name" not in bootstrap_entry:
            raise GitOpsException("Every bootstrap entry must have a 'name' property.")


def create_root_repo(root_repo: GitRepo) -> "RootRepo":
    root_repo_tenants = __load_tenants_from_bootstrap_values(root_repo)
    return RootRepo(root_repo_tenants)
