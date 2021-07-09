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

    api_version: int
    application_name: str

    preview_host_template: str

    preview_template_organisation: str
    preview_template_repository: str
    preview_template_path: str

    preview_target_organisation: str
    preview_target_repository: str

    replacements: List[Replacement]

    def __post_init__(self) -> None:
        assert isinstance(self.application_name, str), "application_name of wrong type!"
        assert isinstance(self.preview_host_template, str), "preview_host_template of wrong type!"
        assert isinstance(self.preview_template_organisation, str), "preview_template_organisation of wrong type!"
        assert isinstance(self.preview_template_repository, str), "preview_template_repository of wrong type!"
        assert isinstance(self.preview_template_path, str), "preview_template_path of wrong type!"
        assert isinstance(self.preview_target_organisation, str), "preview_target_organisation of wrong type!"
        assert isinstance(self.preview_target_repository, str), "preview_target_repository of wrong type!"
        assert isinstance(self.replacements, list), "replacements of wrong type!"
        for index, replacement in enumerate(self.replacements):
            assert isinstance(replacement, self.Replacement), f"replacement[{index}] of wrong type!"

    def get_preview_host(self, preview_id: str) -> str:
        hashed_preview_id = self.create_hashed_preview_id(preview_id)
        return self.preview_host_template.replace("{SHA256_8CHAR_BRANCH_HASH}", hashed_preview_id)

    def get_preview_namespace(self, preview_id: str) -> str:
        hashed_preview_id = self.create_hashed_preview_id(preview_id)
        return f"{self.application_name}-{hashed_preview_id}-preview"

    def is_preview_template_equal_target(self) -> bool:
        return (
            self.preview_template_organisation == self.preview_target_organisation
            and self.preview_template_repository == self.preview_target_repository
        )

    @staticmethod
    def create_hashed_preview_id(preview_id: str) -> str:
        return hashlib.sha256(preview_id.encode("utf-8")).hexdigest()[:8]

    @staticmethod
    def from_yaml(yaml: Any) -> "GitOpsConfig":
        return _GitOpsConfigYamlParser(yaml).parse()


class _GitOpsConfigYamlParser:
    def __init__(self, yaml: Any):
        self.__yaml = yaml

    def __get_value(self, key: str) -> Any:
        keys = key.split(".")
        data = self.__yaml
        for k in keys:
            if not isinstance(data, dict) or k not in data:
                raise GitOpsException(f"Key '{key}' not found in GitOps config!")
            data = data[k]
        return data

    def __get_string_value(self, key: str) -> str:
        value = self.__get_value(key)
        if not isinstance(value, str):
            raise GitOpsException(f"Item '{key}' should be a string in GitOps config!")
        return value

    def __get_list_value(self, key: str) -> List[Any]:
        value = self.__get_value(key)
        if not isinstance(value, list):
            raise GitOpsException(f"Item '{key}' should be a list in GitOps config!")
        return value

    def parse(self) -> GitOpsConfig:
        replacements: List[GitOpsConfig.Replacement] = []
        replacement_dicts = self.__get_list_value("previewConfig.replace")
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

        application_name = self.__get_string_value("deploymentConfig.applicationName")
        preview_target_organisation = self.__get_string_value("deploymentConfig.org")
        preview_target_repository = self.__get_string_value("deploymentConfig.repository")

        return GitOpsConfig(
            api_version=0,
            application_name=application_name,
            preview_host_template=self.__get_string_value("previewConfig.route.host.template"),
            preview_template_organisation=preview_target_organisation,
            preview_template_repository=preview_target_repository,
            preview_template_path=f".preview-templates/{application_name}",
            preview_target_organisation=preview_target_organisation,
            preview_target_repository=preview_target_repository,
            replacements=replacements,
        )
