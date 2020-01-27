import os
import pprint

from ruamel.yaml import YAML

from gitopscli.yaml_util import merge_yaml_element


def sync_apps(apps_git, root_git):
    apps_git.checkout("master")
    full_file_path = apps_git.get_full_file_path(".")
    apps = get_application_directories(full_file_path)

    root_git.checkout("master")
    bootstrap_values_file = root_git.get_full_file_path("bootstrap/values.yaml")

    yaml = YAML()
    path_to_app_config = {}
    all_other_apps = []
    app_config_path = None
    app_file_name = None
    selected_app_config = None
    with open(bootstrap_values_file, "r") as stream:
        bootstrap = yaml.load(stream)
    for boot_entry in bootstrap["bootstrap"]:
        file = "apps/" + boot_entry["name"] + ".yaml"
        apps_config_file = root_git.get_full_file_path(file)

        with open(apps_config_file, "r") as stream:
            app_config_content = yaml.load(stream)
            print(app_config_content["repository"])
            if app_config_content["repository"] == apps_git.get_clone_url():
                app_file_name = file
                selected_app_config = app_config_content
                app_config_path = str(apps_config_file)
            else:
                path_to_app_config[str(apps_config_file)] = app_config_content
                if "applications" in app_config_content and app_config_content["applications"] is not None:
                    all_other_apps += app_config_content["applications"].keys()

    pprint.pprint(all_other_apps)

    if selected_app_config is None:
        raise Exception("Could't find config file with repository " + apps_git.get_clone_url() + " in apps/ directory")

    for app_key in apps:
        if app_key in all_other_apps:
            raise Exception("application: " + app_key + " already exists in a different repository")

    merge_yaml_element(app_config_path, "applications", apps, True)

    root_git.commit("Updated applications in " + app_file_name)
    root_git.push("master")


def get_application_directories(full_file_path):
    app_dirs = [
        name
        for name in os.listdir(full_file_path)
        if os.path.isdir(os.path.join(full_file_path, name)) and not name.startswith(".")
    ]
    apps = {}
    for app_dir in app_dirs:
        apps[app_dir] = {}
    pprint.pprint(apps)
    return apps
