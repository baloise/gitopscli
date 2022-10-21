import os
from dataclasses import dataclass
from ruamel.yaml import YAML
from gitopscli.appconfig_api.traverse_config import traverse_config
from gitopscli.io_api.yaml_util import yaml_file_load, yaml_load


@dataclass
class AppTenantConfig:
    # TODO: rethink objects and class initialization methods
    config_type: str  # is instance initialized as config located in root/team repo
    data: YAML
    # schema important fields
    # config - entrypoint
    # config.repository - tenant repository url
    # config.applications - tenant applications list
    # config.applications.{}.userconfig - user configuration
    name: str  # tenant name
    config_source_repository: str  # team tenant repository url
    # user_config: dict #contents of custom_tenant_config.yaml in team repository
    file_path: str
    file_name: str
    config_api_version: tuple

    def __init__(
        self, config_type, config_source_repository=None, data=None, name=None, file_path=None, file_name=None
    ):
        self.config_type = config_type
        self.config_source_repository = config_source_repository
        if self.config_type == "root":
            self.data = data
            self.file_path = file_path
            self.file_name = file_name
        elif self.config_type == "team":
            self.config_source_repository.clone()
            self.data = self.generate_config_from_team_repo()
        self.config_api_version = self.__get_config_api_version()
        self.name = name

    def __get_config_api_version(self):
        # maybe count the keys?
        if "config" in self.data.keys():
            return ("v2", ("config", "applications"))
        return ("v1", ("applications",))

    def generate_config_from_team_repo(self):
        # recognize type of repo
        team_config_git_repo = self.config_source_repository
        repo_dir = team_config_git_repo.get_full_file_path(".")
        applist = {
            name
            for name in os.listdir(repo_dir)
            if os.path.isdir(os.path.join(repo_dir, name)) and not name.startswith(".")
        }
        # TODO: Create YAML() object without writing template strings
        # Currently this is the easiest method, although it can be better
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
            customconfig = self.get_custom_config(app)
            app_as_yaml_object = yaml_load(template_yaml)
            # dict path hardcoded as object generated will always be in v2 or later
            data["config"]["applications"].update(app_as_yaml_object)
            data["config"]["applications"][app].insert(1, "customAppConfig", customconfig)

        return data

    # TODO: rewrite! as config should be inside of the app folder
    # TODO: method should contain all aps, not only one, requires rewriting of merging during root repo init
    def get_custom_config(self, appname):
        team_config_git_repo = self.config_source_repository
        #        try:
        custom_config_file = team_config_git_repo.get_full_file_path(f"{appname}/app_value_file.yaml")
        #        except Exception as ex:
        # handle missing file
        # handle broken file/nod adhering to allowed
        #            return ex
        # sanitize
        # TODO: how to keep whole content with comments
        # TODO: handling generic values for all apps
        if os.path.exists(custom_config_file):
            custom_config_content = yaml_file_load(custom_config_file)
            return custom_config_content
        return None

    def list_apps(self):
        return traverse_config(self.data, self.config_api_version)

    def add_app(self):
        # adds app to the app tenant config
        pass

    def modify_app(self):
        # modifies existing app in tenant config
        pass

    def delete_app(self):
        # deletes app from tenant config
        pass
