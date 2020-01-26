import os
import pprint

from ruamel.yaml import YAML

from gitopscli.yaml_util import merge_yaml_element


class AppsSynchronizer:

    def sync_apps(self, apps_git, root_git):
        apps_git.checkout("master")
        full_file_path = apps_git.get_full_file_path(".")

        app_dirs = [ name for name in os.listdir(full_file_path) if os.path.isdir(os.path.join(full_file_path, name)) and not name.startswith(".")  ]
        apps = {}
        for app_dir in app_dirs:
            apps[app_dir] = {}
        pprint.pprint(apps)

        root_git.checkout("master")
        bootstrap_values_file = root_git.get_full_file_path("bootstrap/values.yaml")
        yaml = YAML()
        with open(bootstrap_values_file, "r") as stream:
            bootstrap = yaml.load(stream)
        apps_configs = []
        for boot_entry in bootstrap["bootstrap"]:
            apps_config_file = root_git.get_full_file_path("apps/" + boot_entry["name"] + ".yaml")
            path_to_app_config = {}
            with open(apps_config_file, "r") as stream:
                app_config = yaml.load(stream)
                path_to_app_config[str(apps_config_file)] = app_config
            apps_configs.append(app_config)
        app_config_path = None
        selected_app_config = None
        for path, app_config in path_to_app_config.items():
            print( app_config["repository"] )
            if app_config["repository"] == apps_git.get_clone_url():
                selected_app_config = app_config
                app_config_path = path
        if selected_app_config is None:
            raise Exception("Could't find config file with repository " + app_config["repository"] + " in apps/ directory")

        merge_yaml_element(app_config_path, "applications", apps, True)

        root_git.commit("Updated applications in " + app_config_path)
        root_git.push("master")

