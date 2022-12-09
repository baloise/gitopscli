import logging
import os
from typing import Any
from dataclasses import dataclass
from ruamel.yaml.comments import CommentedMap
from gitopscli.git_api import GitApiConfig, GitRepo, GitRepoApiFactory
from gitopscli.io_api.yaml_util import merge_yaml_element
from gitopscli.gitops_exception import GitOpsException
from gitopscli.appconfig_api.traverse_config import traverse_config
from gitopscli.io_api.yaml_util import yaml_file_load, yaml_load
from .command import Command


@dataclass
class AppTenantConfigApiVersion:
    version: str
    path: tuple[str, ...]


class AppTenantConfigFactory:
    def generate_config_from_team_repo(
        self, team_config_git_repo: GitRepo
    ) -> Any:  # TODO: supposed to be ruamel object than Any  pylint: disable=fixme
        repo_dir = team_config_git_repo.get_full_file_path(".")
        applist = {
            name
            for name in os.listdir(repo_dir)
            if os.path.isdir(os.path.join(repo_dir, name)) and not name.startswith(".")
        }
        # TODO: Create YAML() object without writing template strings  pylint: disable=fixme
        template_yaml = """
        config: 
            repository: {}
            applications: {{}}
        """.format(
            team_config_git_repo.get_clone_url()
        )
        data = yaml_load(template_yaml)
        for app in applist:
            template_yaml = """
            {}: {{}}
            """.format(
                app
            )
            customconfig = self.get_custom_config(app, team_config_git_repo)
            app_as_yaml_object = yaml_load(template_yaml)
            # dict path hardcoded as object generated will always be in v2 or later
            data["config"]["applications"].update(app_as_yaml_object)
            if customconfig:
                data["config"]["applications"][app].insert(1, "customAppConfig", customconfig)
        return data

    # TODO: method should contain all aps, not only one, requires rewriting of merging during root repo init  pylint: disable=fixme
    @staticmethod
    def get_custom_config(
        appname: str, team_config_git_repo: GitRepo
    ) -> Any | None:  # TODO: supposed to be ordereddict instead of Any from ruamel pylint: disable=fixme
        #        try:
        custom_config_file = team_config_git_repo.get_full_file_path(f"{appname}/app_value_file.yaml")
        #        except Exception as ex:
        # handle missing file
        # handle broken file/nod adhering to allowed
        #            return ex
        # sanitize
        # TODO: how to keep whole content with comments  pylint: disable=fixme
        # TODO: handling generic values for all apps  pylint: disable=fixme
        if os.path.exists(custom_config_file):
            custom_config_content = yaml_file_load(custom_config_file)
            return custom_config_content
        return None

    @staticmethod
    def create_root_repo_tenant_config(
        name: str,
        data: CommentedMap | dict[Any, Any],
        file_name: str,
        file_path: str,
        found_apps_path: str = "config.applications",
    ) -> "AppTenantConfig":
        return AppTenantConfig(
            config_type="root",
            data=data,
            name=name,
            found_apps_path=found_apps_path,
            file_name=file_name,
            file_path=file_path,
        )

    def create_team_repo_tenant_config(
        self,
        name: str,
        config_source_repository: Any,
        # found_apps_path: str = "config.applications",
    ) -> "AppTenantConfig":
        config_source_repository.clone()
        data = self.generate_config_from_team_repo(config_source_repository)
        return AppTenantConfig(
            config_type="team", data=data, name=name, config_source_repository=config_source_repository.get_clone_url()
        )


@dataclass
class AppTenantConfig:
    config_type: str  # is instance initialized as config located in root/team repo
    data: CommentedMap | dict[Any, Any]  # TODO: supposed to be ordereddict from ruamel pylint: disable=fixme
    name: str  # tenant name
    config_api_version: AppTenantConfigApiVersion = AppTenantConfigApiVersion("v2", ("config", "applications"))
    config_source_repository: str = ""
    file_name: str = ""
    found_apps_path: str = ""
    file_path: str = ""  # team tenant repository url

    def __post_init__(self) -> None:
        self.config_api_version = self.__get_config_api_version()

    def __get_config_api_version(self) -> AppTenantConfigApiVersion:
        if "config" in self.data.keys():
            return AppTenantConfigApiVersion("v2", ("config", "applications"))
        return AppTenantConfigApiVersion("v1", ("applications",))

    def list_apps(self) -> Any:
        return dict(traverse_config(self.data, self.config_api_version.path))

    def add_app(self) -> None:
        # adds app to the app tenant config
        pass

    def modify_app(self) -> None:
        # modifies existing app in tenant config
        pass

    def delete_app(self) -> None:
        # deletes app from tenant config
        pass

    # def get_sanitized_app_tenant_config(self):
    #    self.data
    #    pass


class RootRepoFactory:
    @staticmethod
    def __get_bootstrap_entries(bootstrap_values_file: str) -> list[Any]:
        try:
            bootstrap_yaml = yaml_file_load(bootstrap_values_file)
        except FileNotFoundError as ex:
            raise GitOpsException("File 'bootstrap/values.yaml' not found in root repository.") from ex
        if "bootstrap" in bootstrap_yaml:
            return RootRepoFactory.bootstrap_name_validator(bootstrap_yaml["bootstrap"])
        if "config" in bootstrap_yaml and "bootstrap" in bootstrap_yaml["config"]:
            return RootRepoFactory.bootstrap_name_validator(bootstrap_yaml["config"]["bootstrap"])
        raise GitOpsException("Cannot find key 'bootstrap' or 'config.bootstrap' in 'bootstrap/values.yaml'")

    @staticmethod
    def bootstrap_name_validator(bootstrap_entries: list[Any]) -> list[Any]:
        for bootstrap_entry in bootstrap_entries:
            if "name" not in bootstrap_entry:
                raise GitOpsException("Every bootstrap entry must have a 'name' property.")
        return bootstrap_entries

    @staticmethod
    def __generate_tenant_app_dict_from_root_repo(
        root_config_git_repo: GitRepo, bootstrap: Any
    ) -> dict[str, "AppTenantConfig"]:
        tenant_app_dict = {}
        for bootstrap_entry in bootstrap:
            tenant_apps_config_file_name = "apps/" + bootstrap_entry["name"] + ".yaml"
            logging.info("Analyzing %s in root repository", tenant_apps_config_file_name)
            tenant_apps_config_file = root_config_git_repo.get_full_file_path(tenant_apps_config_file_name)
            try:
                tenant_apps_config_content = yaml_file_load(tenant_apps_config_file)
            except FileNotFoundError as ex:
                raise GitOpsException(f"File '{tenant_apps_config_file_name}' not found in root repository.") from ex
            # TODO exception handling for malformed yaml pylint: disable=fixme
            found_apps_path = "applications"
            if "config" in tenant_apps_config_content:
                tenant_apps_config_content = tenant_apps_config_content["config"]
                found_apps_path = "config.applications"
            if "repository" not in tenant_apps_config_content:
                raise GitOpsException(f"Cannot find key 'repository' in '{tenant_apps_config_file_name}'")
            logging.info("adding %s", (bootstrap_entry["name"]))
            atc = AppTenantConfigFactory().create_root_repo_tenant_config(
                data=tenant_apps_config_content,
                name=bootstrap_entry["name"],
                file_path=tenant_apps_config_file,
                file_name=tenant_apps_config_file_name,
                found_apps_path=found_apps_path,
            )
            tenant_app_dict.update({bootstrap_entry["name"]: atc})
        return tenant_app_dict

    # TODO SHOULD THIS FULL METHOD INSTEAD OF POPULATING  pylint: disable=fixme
    @staticmethod
    def __get_all_apps_list(tenant_dict: Any) -> dict[str, list[Any]]:
        all_apps_list = dict()
        for tenant in tenant_dict:
            value = traverse_config(tenant_dict[tenant].data, tenant_dict[tenant].config_api_version.path)
            all_apps_list.update({tenant: list((dict(value).keys()))})
        return all_apps_list

    def create(self, root_repo: GitRepo) -> "RootRepo":
        name = root_repo.get_clone_url().split("/")[-1].removesuffix(".git")
        root_repo.clone()
        bootstrap_values_file = root_repo.get_full_file_path("bootstrap/values.yaml")
        bootstrap = self.__get_bootstrap_entries(bootstrap_values_file)
        tenant_dict = self.__generate_tenant_app_dict_from_root_repo(root_repo, bootstrap)
        all_app_list = self.__get_all_apps_list(tenant_dict)
        return RootRepo(name, tenant_dict, bootstrap, all_app_list)


@dataclass
class RootRepo:
    name: str  # root repository name
    tenant_dict: dict[
        str, "AppTenantConfig"
    ]  # TODO of AppTenantConfig #list of the tenant configs in the root repository (in apps folder)  pylint: disable=fixme
    bootstrap: list[Any]  # list of tenants to be bootstrapped, derived form values.yaml in bootstrap root repo dict
    all_app_list: dict[str, list[Any]]  # list of apps without custormer separation

    def list_tenants(self) -> list[str]:
        return list(self.tenant_dict.keys())


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


def __validate_if_app_not_present(
    apps_from_other_repos: dict[Any, Any], team_config_app_name: str, tenant_config_repo_apps: Any
) -> None:
    apps_from_other_repos.pop(team_config_app_name)
    for app in list(tenant_config_repo_apps.keys()):
        for tenant in apps_from_other_repos.values():
            if app in tenant:
                raise GitOpsException(f"Application '{app}' already exists in a different repository")


def __sync_apps(team_config_git_repo: GitRepo, root_config_git_repo: GitRepo, git_user: str, git_email: str) -> None:
    logging.info("Team config repository: %s", team_config_git_repo.get_clone_url())
    logging.info("Root config repository: %s", root_config_git_repo.get_clone_url())

    root_repo = RootRepoFactory().create(root_repo=root_config_git_repo)
    team_config_app_name = team_config_git_repo.get_clone_url().split("/")[-1].removesuffix(".git")
    if not team_config_app_name in root_repo.list_tenants():
        raise GitOpsException("Couldn't find config file for apps repository in root repository's 'apps/' directory")
    tenant_config_team_repo = AppTenantConfigFactory().create_team_repo_tenant_config(
        name=team_config_app_name, config_source_repository=team_config_git_repo
    )

    tenant_config_repo_apps = tenant_config_team_repo.list_apps()
    __validate_if_app_not_present(root_repo.all_app_list.copy(), team_config_app_name, tenant_config_repo_apps)

    logging.info(
        "Found %s app(s) in apps repository: %s", len(tenant_config_repo_apps), ", ".join(tenant_config_repo_apps)
    )
    logging.info("Searching apps repository in root repository's 'apps/' directory...")

    current_repo_apps = root_repo.tenant_dict[team_config_app_name].list_apps()
    for app in list(current_repo_apps.keys()):
        if (
            current_repo_apps.get(app) is not None
        ):  # None is returend when application does not have any additional parameters
            custom_app_config_item = current_repo_apps[app].get("customAppConfig")
            current_repo_apps[app].clear()
            if (
                custom_app_config_item is not None
            ):  # None is returend when application does not have custom configuration
                current_repo_apps[app]["customAppConfig"] = custom_app_config_item

    if current_repo_apps == tenant_config_repo_apps:
        logging.info("Root repository already up-to-date. I'm done here.")
        return

    apps_config_file = root_repo.tenant_dict[team_config_app_name].file_path
    apps_config_file_name = root_repo.tenant_dict[team_config_app_name].file_name
    logging.info("Sync applications in root repository's %s.", apps_config_file_name)
    merge_yaml_element(
        apps_config_file,
        root_repo.tenant_dict[team_config_app_name].found_apps_path,
        {
            repo_app: traverse_config(
                tenant_config_team_repo.data, tenant_config_team_repo.config_api_version.path
            ).get(repo_app, "{}")
            for repo_app in tenant_config_repo_apps
        },
    )

    __commit_and_push(team_config_git_repo, root_config_git_repo, git_user, git_email, apps_config_file_name)


def __commit_and_push(
    team_config_git_repo: GitRepo, root_config_git_repo: GitRepo, git_user: str, git_email: str, app_file_name: str
) -> None:
    author = team_config_git_repo.get_author_from_last_commit()
    root_config_git_repo.commit(git_user, git_email, f"{author} updated " + app_file_name)
    root_config_git_repo.push()
