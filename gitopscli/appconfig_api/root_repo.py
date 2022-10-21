from dataclasses import dataclass
import logging
from typing import Any
from gitopscli.git_api import GitRepo
from gitopscli.gitops_exception import GitOpsException
from gitopscli.io_api.yaml_util import yaml_file_load
from gitopscli.appconfig_api.app_tenant_config import AppTenantConfig
from gitopscli.appconfig_api.traverse_config import traverse_config


@dataclass
class RootRepo:
    name: str  # root repository name
    tenant_list: dict  # TODO of AppTenantConfig #list of the tenant configs in the root repository (in apps folder)
    bootstrap: set  # list of tenants to be bootstrapped, derived form values.yaml in bootstrap root repo dict
    app_list: set  # llist of apps without custormer separation

    def __init__(self, root_config_git_repo: GitRepo):
        repo_clone_url = root_config_git_repo.get_clone_url()
        root_config_git_repo.clone()
        bootstrap_values_file = root_config_git_repo.get_full_file_path("bootstrap/values.yaml")
        self.bootstrap = self.__get_bootstrap_entries(bootstrap_values_file)
        self.name = repo_clone_url.split("/")[-1].removesuffix(".git")
        self.tenant_list = self.__generate_tenant_app_dict(root_config_git_repo)
        self.app_list = self.__get_all_apps_list()

    def __get_bootstrap_entries(self, bootstrap_values_file: str) -> Any:
        try:
            bootstrap_yaml = yaml_file_load(bootstrap_values_file)
        except FileNotFoundError as ex:
            raise GitOpsException("File 'bootstrap/values.yaml' not found in root repository.") from ex
        if "bootstrap" not in bootstrap_yaml:
            raise GitOpsException("Cannot find key 'bootstrap' in 'bootstrap/values.yaml'")
        for bootstrap_entry in bootstrap_yaml["bootstrap"]:
            if "name" not in bootstrap_entry:
                raise GitOpsException("Every bootstrap entry must have a 'name' property.")
        return bootstrap_yaml["bootstrap"]

    def __generate_tenant_app_dict(self, root_config_git_repo: GitRepo):
        tenant_app_dict = {}
        for bootstrap_entry in self.bootstrap:
            tenant_apps_config_file_name = "apps/" + bootstrap_entry["name"] + ".yaml"
            logging.info("Analyzing %s in root repository", tenant_apps_config_file_name)
            tenant_apps_config_file = root_config_git_repo.get_full_file_path(tenant_apps_config_file_name)
            try:
                tenant_apps_config_content = yaml_file_load(tenant_apps_config_file)
            except FileNotFoundError as ex:
                raise GitOpsException(f"File '{tenant_apps_config_file_name}' not found in root repository.") from ex
            # TODO exception handling for malformed yaml
            if "config" in tenant_apps_config_content:
                tenant_apps_config_content = tenant_apps_config_content["config"]
            if "repository" not in tenant_apps_config_content:
                raise GitOpsException(f"Cannot find key 'repository' in '{tenant_apps_config_file_name}'")
            # if "config" in tenant_apps_config_content:
            logging.info("adding {}".format(bootstrap_entry["name"]))
            atc = AppTenantConfig(
                data=tenant_apps_config_content,
                name=bootstrap_entry["name"],
                config_type="root",
                file_path=tenant_apps_config_file,
                file_name=tenant_apps_config_file_name,
            )
            tenant_app_dict.update({bootstrap_entry["name"]: atc})
        return tenant_app_dict

    def __get_all_apps_list(self):
        all_apps_list = dict()
        for tenant in self.tenant_list:
            value = traverse_config(self.tenant_list[tenant].data, self.tenant_list[tenant].config_api_version)
            all_apps_list.update({tenant: list((dict(value).keys()))})
        return all_apps_list
