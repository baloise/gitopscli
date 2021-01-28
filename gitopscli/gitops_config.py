import hashlib
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Any

from gitopscli.gitops_exception import GitOpsException


@dataclass(frozen=True)
class GitOpsConfig:
    @dataclass(frozen=True)
    class Replacement:
        class Variable(Enum):
            GIT_COMMIT = auto()
            ROUTE_HOST = auto()

        path: str
        variable: Variable

        def __post_init__(self) -> None:
            assert isinstance(self.path, str), "path of wrong type!"
            assert isinstance(self.variable, self.Variable), "variable of wrong type!"

    application_name: str
    team_config_org: str
    team_config_repo: str
    route_host_template: str
    replacements: List[Replacement]

    def __post_init__(self) -> None:
        assert isinstance(self.application_name, str), "application_name of wrong type!"
        assert isinstance(self.team_config_org, str), "team_config_org of wrong type!"
        assert isinstance(self.team_config_repo, str), "team_config_repo of wrong type!"
        assert isinstance(self.route_host_template, str), "route_host_template of wrong type!"
        assert isinstance(self.replacements, list), "replacements of wrong type!"
        for index, replacement in enumerate(self.replacements):
            assert isinstance(replacement, self.Replacement), f"replacement[{index}] of wrong type!"

    def get_route_host(self, preview_id: str) -> str:
        hashed_preview_id = self.create_hashed_preview_id(preview_id)
        return self.route_host_template.replace("{SHA256_8CHAR_BRANCH_HASH}", hashed_preview_id)

    def get_preview_namespace(self, preview_id: str) -> str:
        hashed_preview_id = self.create_hashed_preview_id(preview_id)
        return f"{self.application_name}-{hashed_preview_id}-preview"

    @staticmethod
    def create_hashed_preview_id(preview_id: str) -> str:
        return hashlib.sha256(preview_id.encode("utf-8")).hexdigest()[:8]

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
            variable_str = replacement_dict["variable"]
            if not isinstance(path, str):
                raise GitOpsException(
                    f"Item 'previewConfig.replace.[{index}].path' should be a string in GitOps config!"
                )
            if not isinstance(variable_str, str):
                raise GitOpsException(
                    f"Item 'previewConfig.replace.[{index}].variable' should be a string in GitOps config!"
                )
            try:
                variable = GitOpsConfig.Replacement.Variable[variable_str]
            except KeyError as ex:
                possible_values = ", ".join(sorted([v.name for v in GitOpsConfig.Replacement.Variable]))
                raise GitOpsException(
                    f"Item 'previewConfig.replace.[{index}].variable' should be one of the following values in "
                    f"GitOps config: {possible_values}"
                ) from ex
            replacements.append(GitOpsConfig.Replacement(path=path, variable=variable))

        return GitOpsConfig(
            application_name=get_string_value("deploymentConfig.applicationName"),
            team_config_org=get_string_value("deploymentConfig.org"),
            team_config_repo=get_string_value("deploymentConfig.repository"),
            route_host_template=get_string_value("previewConfig.route.host.template"),
            replacements=replacements,
        )
