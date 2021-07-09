import re
import hashlib
from dataclasses import dataclass
from typing import List, Any, Optional, Dict, Callable

from gitopscli.gitops_exception import GitOpsException


@dataclass(frozen=True)
class GitOpsConfig:
    class Replacement:
        @dataclass(frozen=True)
        class Context:
            gitops_config: "GitOpsConfig"
            preview_id: str
            git_hash: str

        __VARIABLE_REGEX = re.compile(r"{(\w+)}")
        __VARIABLE_MAPPERS: Dict[str, Callable[["GitOpsConfig.Replacement.Context"], str]] = {
            "GIT_HASH": lambda context: context.git_hash,
            "PREVIEW_HOST": lambda context: context.gitops_config.get_preview_host(context.preview_id),
            "PREVIEW_NAMESPACE": lambda context: context.gitops_config.get_preview_namespace(context.preview_id),
        }

        def __init__(self, path: str, value_template: str):
            assert isinstance(path, str), "path of wrong type!"
            assert isinstance(value_template, str), "value_template of wrong type!"

            self.path = path
            self.value_template = value_template

            for var in self.__VARIABLE_REGEX.findall(self.value_template):
                if var not in self.__VARIABLE_MAPPERS.keys():
                    raise GitOpsException(
                        f"Replacement value '{self.value_template}' for path '{self.path}' "
                        f"contains invalid variable: {var}"
                    )

        def get_value(self, context: Context) -> str:
            val = self.value_template
            for variable, value_func in self.__VARIABLE_MAPPERS.items():
                val = val.replace(f"{{{variable}}}", value_func(context))
            return val

    api_version: int
    application_name: str

    preview_host_template: str

    preview_template_organisation: str
    preview_template_repository: str
    preview_template_path: str
    preview_template_branch: Optional[str]

    preview_target_organisation: str
    preview_target_repository: str
    preview_target_branch: Optional[str]
    preview_target_namespace_template: str

    replacements: Dict[str, List[Replacement]]

    def __post_init__(self) -> None:
        assert isinstance(self.application_name, str), "application_name of wrong type!"
        assert isinstance(self.preview_host_template, str), "preview_host_template of wrong type!"
        assert isinstance(self.preview_template_organisation, str), "preview_template_organisation of wrong type!"
        assert isinstance(self.preview_template_repository, str), "preview_template_repository of wrong type!"
        assert isinstance(self.preview_template_path, str), "preview_template_path of wrong type!"
        if self.preview_template_branch is not None:
            assert isinstance(self.preview_template_branch, str), "preview_template_branch of wrong type!"
        assert isinstance(self.preview_target_organisation, str), "preview_target_organisation of wrong type!"
        assert isinstance(self.preview_target_repository, str), "preview_target_repository of wrong type!"
        if self.preview_target_branch is not None:
            assert isinstance(self.preview_target_branch, str), "preview_target_branch of wrong type!"
        assert isinstance(
            self.preview_target_namespace_template, str
        ), "preview_target_namespace_template of wrong type!"
        assert isinstance(self.replacements, dict), "replacements of wrong type!"
        for file, replacements in self.replacements.items():
            assert isinstance(file, str), f"replacement file '{file}' of wrong type!"
            for index, replacement in enumerate(replacements):
                assert isinstance(replacement, self.Replacement), f"replacement[{file}][{index}] of wrong type!"

    def get_preview_host(self, preview_id: str) -> str:
        preview_id_hash = self.create_preview_id_hash(preview_id)
        return self.preview_host_template.replace("{PREVIEW_ID_HASH}", preview_id_hash)

    def get_preview_namespace(self, preview_id: str) -> str:
        preview_id_hash = self.create_preview_id_hash(preview_id)
        return self.preview_target_namespace_template.replace("{PREVIEW_ID_HASH}", preview_id_hash)

    def is_preview_template_equal_target(self) -> bool:
        return (
            self.preview_template_organisation == self.preview_target_organisation
            and self.preview_template_repository == self.preview_target_repository
            and self.preview_template_branch == self.preview_target_branch
        )

    @staticmethod
    def create_preview_id_hash(preview_id: str) -> str:
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
        replacements: Dict[str, List[GitOpsConfig.Replacement]] = {
            "Chart.yaml": [GitOpsConfig.Replacement("name", "{PREVIEW_NAMESPACE}")],
            "values.yaml": [],
        }
        replacement_dicts = self.__get_list_value("previewConfig.replace")
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
            if "{" in variable or "}" in variable:
                raise GitOpsException(f"Item 'previewConfig.replace.[{index}].variable' must not contain '{{' or '}}'!")
            if variable == "ROUTE_HOST":
                variable = "PREVIEW_HOST"  # backwards compatability
            if variable == "GIT_COMMIT":
                variable = "GIT_HASH"  # backwards compatability
            replacements["values.yaml"].append(GitOpsConfig.Replacement(path, f"{{{variable}}}"))

        application_name = self.__get_string_value("deploymentConfig.applicationName")
        preview_target_organisation = self.__get_string_value("deploymentConfig.org")
        preview_target_repository = self.__get_string_value("deploymentConfig.repository")

        return GitOpsConfig(
            api_version=0,
            application_name=application_name,
            preview_host_template=self.__get_string_value("previewConfig.route.host.template").replace(
                "{SHA256_8CHAR_BRANCH_HASH}", "{PREVIEW_ID_HASH}"  # backwards compatibility
            ),
            preview_template_organisation=preview_target_organisation,
            preview_template_repository=preview_target_repository,
            preview_template_path=f".preview-templates/{application_name}",
            preview_template_branch=None,  # use default branch
            preview_target_organisation=preview_target_organisation,
            preview_target_repository=preview_target_repository,
            preview_target_branch=None,  # use default branch
            preview_target_namespace_template=f"{application_name}-{{PREVIEW_ID_HASH}}-preview",
            replacements=replacements,
        )
