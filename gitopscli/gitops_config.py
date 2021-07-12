import re
import hashlib
from dataclasses import dataclass
from typing import List, Any, Optional, Dict, Callable, Set

from gitopscli.gitops_exception import GitOpsException

_MAX_NAMESPACE_LENGTH = 63
_VARIABLE_REGEX = re.compile(r"{(\w+)}")


@dataclass(frozen=True)
class GitOpsConfig:
    class Replacement:
        @dataclass(frozen=True)
        class Context:
            gitops_config: "GitOpsConfig"
            preview_id: str
            git_hash: str

        __VARIABLE_MAPPERS: Dict[str, Callable[["GitOpsConfig.Replacement.Context"], str]] = {
            "GIT_HASH": lambda context: context.git_hash,
            "PREVIEW_HOST": lambda context: context.gitops_config.get_preview_host(context.preview_id),
            "PREVIEW_NAMESPACE": lambda context: context.gitops_config.get_preview_namespace(context.preview_id),
            "APPLICATION_NAME": lambda context: context.gitops_config.application_name,
            "PREVIEW_ID": lambda context: context.preview_id,
            "PREVIEW_ID_HASH": lambda context: GitOpsConfig.create_preview_id_hash(context.preview_id),
        }

        def __init__(self, path: str, value_template: str):
            assert isinstance(path, str), "path of wrong type!"
            assert isinstance(value_template, str), "value_template of wrong type!"

            self.path = path
            self.value_template = value_template

            for var in _VARIABLE_REGEX.findall(self.value_template):
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
    preview_template_path_template: str
    preview_template_branch: Optional[str]

    preview_target_organisation: str
    preview_target_repository: str
    preview_target_branch: Optional[str]
    preview_target_namespace_template: str

    replacements: Dict[str, List[Replacement]]

    @property
    def preview_template_path(self) -> str:
        return self.preview_template_path_template.replace("{APPLICATION_NAME}", self.application_name)

    def __post_init__(self) -> None:
        assert isinstance(self.application_name, str), "application_name of wrong type!"
        assert isinstance(self.preview_host_template, str), "preview_host_template of wrong type!"
        self.__assert_variables(
            self.preview_host_template, {"APPLICATION_NAME", "PREVIEW_ID_HASH", "PREVIEW_ID", "PREVIEW_NAMESPACE"}
        )
        assert isinstance(self.preview_template_organisation, str), "preview_template_organisation of wrong type!"
        assert isinstance(self.preview_template_repository, str), "preview_template_repository of wrong type!"
        assert isinstance(self.preview_template_path_template, str), "preview_template_path_template of wrong type!"
        self.__assert_variables(self.preview_template_path_template, {"APPLICATION_NAME"})
        if self.preview_template_branch is not None:
            assert isinstance(self.preview_template_branch, str), "preview_template_branch of wrong type!"
        assert isinstance(self.preview_target_organisation, str), "preview_target_organisation of wrong type!"
        assert isinstance(self.preview_target_repository, str), "preview_target_repository of wrong type!"
        if self.preview_target_branch is not None:
            assert isinstance(self.preview_target_branch, str), "preview_target_branch of wrong type!"
        assert isinstance(
            self.preview_target_namespace_template, str
        ), "preview_target_namespace_template of wrong type!"
        self.__assert_variables(
            self.preview_target_namespace_template, {"APPLICATION_NAME", "PREVIEW_ID_HASH", "PREVIEW_ID"}
        )
        assert isinstance(self.replacements, dict), "replacements of wrong type!"
        for file, replacements in self.replacements.items():
            assert isinstance(file, str), f"replacement file '{file}' of wrong type!"
            for index, replacement in enumerate(replacements):
                assert isinstance(replacement, self.Replacement), f"replacement[{file}][{index}] of wrong type!"

    def get_preview_host(self, preview_id: str) -> str:
        preview_host = self.preview_host_template
        preview_host = preview_host.replace("{APPLICATION_NAME}", self.application_name)
        preview_host = preview_host.replace("{PREVIEW_ID_HASH}", self.create_preview_id_hash(preview_id))
        preview_host = preview_host.replace("{PREVIEW_ID}", self.__sanitize(preview_id))
        preview_host = preview_host.replace("{PREVIEW_NAMESPACE}", self.get_preview_namespace(preview_id))
        return preview_host

    def get_preview_namespace(self, preview_id: str) -> str:
        preview_namespace = self.preview_target_namespace_template
        preview_namespace = preview_namespace.replace("{APPLICATION_NAME}", self.application_name)
        preview_namespace = preview_namespace.replace("{PREVIEW_ID_HASH}", self.create_preview_id_hash(preview_id))

        current_length = len(preview_namespace) - len("{PREVIEW_ID}")
        remaining_length = _MAX_NAMESPACE_LENGTH - current_length
        sanitized_preview_id = self.__sanitize(preview_id, remaining_length)

        preview_namespace = preview_namespace.replace("{PREVIEW_ID}", sanitized_preview_id)
        preview_namespace = preview_namespace.lower()

        invalid_character = re.search(r"[^a-z0-9-]", preview_namespace)
        if invalid_character:
            raise GitOpsException(f"Invalid character in preview namespace: '{invalid_character[0]}'")
        return preview_namespace

    @staticmethod
    def __assert_variables(template: str, variables: Set[str]) -> None:
        for var in _VARIABLE_REGEX.findall(template):
            if var not in variables:
                raise GitOpsException(f"GitOps config template '{template}' contains invalid variable: {var}")

    @staticmethod
    def __sanitize(preview_id: str, max_length: Optional[int] = None) -> str:
        sanitized_preview_id = preview_id.lower()
        sanitized_preview_id = re.sub(r"[^a-z0-9-]", "-", sanitized_preview_id)
        sanitized_preview_id = re.sub(r"-+", "-", sanitized_preview_id)
        if max_length is not None:
            sanitized_preview_id = sanitized_preview_id[0:max_length]
        sanitized_preview_id = re.sub(r"-$", "", sanitized_preview_id)
        return sanitized_preview_id

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

    def __get_value_or_default(self, key: str, default: Optional[Any]) -> Optional[Any]:
        try:
            return self.__get_value(key)
        except GitOpsException:
            return default

    def __get_string_value(self, key: str) -> str:
        value = self.__get_value(key)
        if not isinstance(value, str):
            raise GitOpsException(f"Item '{key}' should be a string in GitOps config!")
        return value

    def __get_string_value_or_default(self, key: str, default: str) -> str:
        value = self.__get_value_or_default(key, default)
        if not isinstance(value, str):
            raise GitOpsException(f"Item '{key}' should be a string in GitOps config!")
        return value

    def __get_string_value_or_none(self, key: str) -> Optional[str]:
        value = self.__get_value_or_default(key, None)
        if not isinstance(value, str) and value is not None:
            raise GitOpsException(f"Item '{key}' should be a string in GitOps config!")
        return value

    def __get_list_value(self, key: str) -> List[Any]:
        value = self.__get_value(key)
        if not isinstance(value, list):
            raise GitOpsException(f"Item '{key}' should be a list in GitOps config!")
        return value

    def __get_dict_value(self, key: str) -> Dict[str, Any]:
        value = self.__get_value(key)
        if not isinstance(value, dict):
            raise GitOpsException(f"Item '{key}' should be an object in GitOps config!")
        return value

    def parse(self) -> GitOpsConfig:
        api_version = self.__get_string_value_or_default("apiVersion", "v0")
        if api_version == "v0":
            return self.__parse_v0()
        if api_version == "v1":
            return self.__parse_v1()
        raise GitOpsException(f"GitOps config apiVersion '{api_version}' is not supported!")

    def __parse_v0(self) -> GitOpsConfig:
        replacements: Dict[str, List[GitOpsConfig.Replacement]] = {
            "Chart.yaml": [GitOpsConfig.Replacement("name", "{PREVIEW_NAMESPACE}")],
            "values.yaml": [],
        }
        replacement_dicts = self.__get_list_value("previewConfig.replace")
        for index, replacement_dict in enumerate(replacement_dicts):
            if not isinstance(replacement_dict, dict):
                raise GitOpsException(f"Item 'previewConfig.replace.[{index}]' should be an object in GitOps config!")
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

        preview_target_organisation = self.__get_string_value("deploymentConfig.org")
        preview_target_repository = self.__get_string_value("deploymentConfig.repository")

        return GitOpsConfig(
            api_version=0,
            application_name=self.__get_string_value("deploymentConfig.applicationName"),
            preview_host_template=self.__get_string_value("previewConfig.route.host.template").replace(
                "{SHA256_8CHAR_BRANCH_HASH}", "{PREVIEW_ID_HASH}"  # backwards compatibility
            ),
            preview_template_organisation=preview_target_organisation,
            preview_template_repository=preview_target_repository,
            preview_template_path_template=f".preview-templates/{{APPLICATION_NAME}}",
            preview_template_branch=None,  # use default branch
            preview_target_organisation=preview_target_organisation,
            preview_target_repository=preview_target_repository,
            preview_target_branch=None,  # use default branch
            preview_target_namespace_template=f"{{APPLICATION_NAME}}-{{PREVIEW_ID_HASH}}-preview",
            replacements=replacements,
        )

    def __parse_v1(self) -> GitOpsConfig:
        preview_target_organisation = self.__get_string_value("previewConfig.target.organisation")
        preview_target_repository = self.__get_string_value("previewConfig.target.repository")
        preview_target_branch = self.__get_string_value_or_none("previewConfig.target.branch")

        replacements: Dict[str, List[GitOpsConfig.Replacement]] = {}
        for filename, file_replacements in self.__get_dict_value("previewConfig.replace").items():
            replacements[filename] = []
            escaped_filename = filename.replace(".", "\\.")
            file_key = f"previewConfig.replace.{escaped_filename}"
            if not isinstance(file_replacements, list):
                raise GitOpsException(f"Item '{file_key}' should be a list in GitOps config!")
            for index, file_replacement in enumerate(file_replacements):
                key = f"{file_key}.[{index}]"
                if not isinstance(file_replacement, dict):
                    raise GitOpsException(f"Item '{key}' should be an object in GitOps config!")
                if "path" not in file_replacement:
                    raise GitOpsException(f"Key '{key}.path' not found in GitOps config!")
                if "value" not in file_replacement:
                    raise GitOpsException(f"Key '{key}.value' not found in GitOps config!")
                path = file_replacement["path"]
                value = file_replacement["value"]
                if not isinstance(path, str):
                    raise GitOpsException(f"Item '{key}.path' should be a string in GitOps config!")
                if not isinstance(value, str):
                    raise GitOpsException(f"Item '{key}.value' should be a string in GitOps config!")
                replacements[filename].append(GitOpsConfig.Replacement(path, value))

        return GitOpsConfig(
            api_version=1,
            application_name=self.__get_string_value("applicationName"),
            preview_host_template=self.__get_string_value("previewConfig.host"),
            preview_template_organisation=self.__get_string_value_or_default(
                "previewConfig.template.organisation", preview_target_organisation
            ),
            preview_template_repository=self.__get_string_value_or_default(
                "previewConfig.template.repository", preview_target_repository
            ),
            preview_template_path_template=self.__get_string_value_or_default(
                "previewConfig.template.path", f".preview-templates/{{APPLICATION_NAME}}"
            ),
            preview_template_branch=self.__get_string_value_or_none("previewConfig.template.branch")
            or preview_target_branch,
            preview_target_organisation=preview_target_organisation,
            preview_target_repository=preview_target_repository,
            preview_target_branch=preview_target_branch,
            preview_target_namespace_template=self.__get_string_value_or_default(
                "previewConfig.target.namespace", f"{{APPLICATION_NAME}}-{{PREVIEW_ID}}-{{PREVIEW_ID_HASH}}-preview"
            ),
            replacements=replacements,
        )
