from dataclasses import dataclass
from typing import List, Any

from gitopscli.gitops_exception import GitOpsException


@dataclass(frozen=True)
class GitOpsConfig:
    @dataclass(frozen=True)
    class Replacement:
        path: str
        variable: str

    application_name: str
    team_config_org: str
    team_config_repo: str
    route_host: str
    replacements: List[Replacement]

    @staticmethod
    def from_yaml(yaml: Any) -> "GitOpsConfig":
        def get_value(key: str) -> Any:
            keys = key.split(".")
            data = yaml
            for k in keys:
                if not isinstance(data, dict) or k not in data:
                    raise GitOpsException(f"Key '{key}' not found in GitOps config!")
                data = data[k]
            return data

        def get_string_value(key: str) -> str:
            value = get_value(key)
            if not isinstance(value, str):
                raise GitOpsException(f"Item '{key}' should be a string in GitOps config!")
            return value

        def get_list_value(key: str) -> List[Any]:
            value = get_value(key)
            if not isinstance(value, list):
                raise GitOpsException(f"Item '{key}' should be a list in GitOps config!")
            return value

        replacements: List[GitOpsConfig.Replacement] = []
        replacement_dicts = get_list_value("previewConfig.replace")
        for index, replacement_dict in enumerate(replacement_dicts):
            if not isinstance(replacement_dict, dict):
                raise GitOpsException(f"Item 'previewConfig.replace.[{index}]' should be a object in GitOps config!")
            if "path" not in replacement_dict:
                raise GitOpsException(f"Key 'previewConfig.replace.[{index}].path' not found in GitOps config!")
            if "variable" not in replacement_dict:
                raise GitOpsException(f"Key 'previewConfig.replace.[{index}].variable' not found in GitOps config!")
            path = replacement_dict["path"]
            variable = replacement_dict["variable"]
            if not isinstance(path, str):
                raise GitOpsException(
                    f"Item 'previewConfig.replace.[{index}].path' should be a string in GitOps config!"
                )
            if not isinstance(variable, str):
                raise GitOpsException(
                    f"Item 'previewConfig.replace.[{index}].variable' should be a string in GitOps config!"
                )
            if variable not in {"GIT_COMMIT", "ROUTE_HOST"}:
                raise GitOpsException(
                    f"Item 'previewConfig.replace.[{index}].variable' should be be either "
                    "'GIT_COMMIT' or 'ROUTE_HOST' in GitOps config!"
                )
            replacements.append(GitOpsConfig.Replacement(path=path, variable=variable))

        return GitOpsConfig(
            application_name=get_string_value("deploymentConfig.applicationName"),
            team_config_org=get_string_value("deploymentConfig.org"),
            team_config_repo=get_string_value("deploymentConfig.repository"),
            route_host=get_string_value("previewConfig.route.host.template"),
            replacements=replacements,
        )
