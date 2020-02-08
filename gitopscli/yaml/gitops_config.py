from .yaml_util import yaml_load


class GitOpsConfig:
    def __init__(self, filename):
        with open(filename, "r") as input_stream:
            self._data = yaml_load(input_stream)

    @property
    def application_name(self):
        return self._data["deploymentConfig"]["applicationName"]

    @property
    def team_config_org(self):
        return self._data["deploymentConfig"]["org"]

    @property
    def team_config_repo(self):
        return self._data["deployment-config"]["repository"]

    @property
    def route_host(self):
        return self._data["previewConfig"]["route"]["host"]["template"]

    @property
    def replacements(self):
        return self._data["previewConfig"]["replace"]
