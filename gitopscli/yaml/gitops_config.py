from .yaml_util import yaml_load


class GitOpsConfig:
    def __init__(self, filename):
        with open(filename, "r") as input_stream:
            self._data = yaml_load(input_stream)

    @property
    def application_name(self):
        return self._data.get("application-name")

    @property
    def team_config_org(self):
        return self._data.get("team-config-org")

    @property
    def team_config_repo(self):
        return self._data.get("team-config-repo")

    @property
    def route_host(self):
        return self._data.get("routehost")

    @property
    def route_paths(self):
        return self._data.get("routepaths", [])

    @property
    def image_paths(self):
        return self._data.get("imagepaths", [])
