from typing import List, Any
from .yaml_util import yaml_load
from ..gitops_exception import GitOpsException


class GitOpsConfig:
    def __init__(self, filename: str) -> None:
        with open(filename, "r") as input_stream:
            yaml_str = input_stream.read()
        self._data = yaml_load(yaml_str)

    @property
    def application_name(self) -> str:
        return self.__get_string_value("deploymentConfig.applicationName")

    @property
    def team_config_org(self) -> str:
        return self.__get_string_value("deploymentConfig.org")

    @property
    def team_config_repo(self) -> str:
        return self.__get_string_value("deploymentConfig.repository")

    @property
    def route_host(self) -> str:
        return self.__get_string_value("previewConfig.route.host.template")

    @property
    def replacements(self) -> List[Any]:
        items = self.__get_list_value("previewConfig.replace")
        for item in items:
            if not isinstance(item, dict) or "path" not in item or "variable" not in item:
                raise GitOpsException(f"Every item in 'previewConfig.replace' should have a 'path' and and 'variabe'!")
        return items

    def __get_string_value(self, key: str) -> str:
        value = self.__get_value(key)
        if not isinstance(value, str):
            raise GitOpsException(f"Key '{key}' should be a string in GitOps config!")
        return value

    def __get_list_value(self, key: str) -> List[Any]:
        value = self.__get_value(key)
        if not isinstance(value, list):
            raise GitOpsException(f"Key '{key}' should be a list in GitOps config!")
        return value

    def __get_value(self, key: str) -> Any:
        keys = key.split(".")
        data = self._data
        for k in keys:
            if not isinstance(data, dict) or k not in data:
                raise GitOpsException(f"Key '{key}' not found in GitOps config!")
            data = data[k]
        return data
