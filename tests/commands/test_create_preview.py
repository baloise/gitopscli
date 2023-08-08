import os
import unittest
import shutil
import logging
from unittest.mock import call, Mock
from gitopscli.io_api.yaml_util import update_yaml_file, YAMLException, yaml_file_dump
from gitopscli.git_api import GitRepo, GitRepoApi, GitRepoApiFactory, GitProvider, GitApiConfig
from gitopscli.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException
from gitopscli.commands.create_preview import CreatePreviewCommand, load_gitops_config
from .mock_mixin import MockMixin

DUMMY_GIT_HASH = "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9"

ARGS = CreatePreviewCommand.Args(
    username="USERNAME",
    password="PASSWORD",
    git_user="GIT_USER",
    git_email="GIT_EMAIL",
    git_author_name="GIT_AUTHOR_NAME",
    git_author_email="GIT_AUTHOR_EMAIL",
    organisation="ORGA",
    repository_name="REPO",
    git_provider=GitProvider.GITHUB,
    git_provider_url=None,
    preview_id="PREVIEW_ID",
    git_hash=DUMMY_GIT_HASH,
)

INFO_YAML = {
    "previewId": "PREVIEW_ID",
    "previewIdHash": "685912d3",
    "routeHost": "app.xy-685912d3.example.tld",
    "namespace": "my-app-685912d3-preview",
}


class CreatePreviewCommandTest(MockMixin, unittest.TestCase):
    def setUp(self):
        self.init_mock_manager(CreatePreviewCommand)

        self.os_mock = self.monkey_patch(os)
        self.os_mock.path.isdir.return_value = True

        self.shutil_mock = self.monkey_patch(shutil)
        self.shutil_mock.copytree.return_value = None

        self.logging_mock = self.monkey_patch(logging)
        self.logging_mock.info.return_value = None

        self.update_yaml_file_mock = self.monkey_patch(update_yaml_file)
        self.update_yaml_file_mock.return_value = True

        self.yaml_file_dump_mock = self.monkey_patch(yaml_file_dump)
        self.yaml_file_dump_mock.return_value = None

        self.load_gitops_config_mock = self.monkey_patch(load_gitops_config)
        self.load_gitops_config_mock.return_value = GitOpsConfig(
            api_version=2,
            application_name="my-app",
            messages_created_template="created template ${PREVIEW_ID_HASH}",
            messages_updated_template="updated template ${PREVIEW_ID_HASH}",
            messages_uptodate_template="uptodate template ${PREVIEW_ID_HASH}",
            preview_host_template="app.xy-${PREVIEW_ID_HASH}.example.tld",
            preview_template_organisation="PREVIEW_TEMPLATE_ORG",
            preview_template_repository="PREVIEW_TEMPLATE_REPO",
            preview_template_path_template=".preview-templates/my-app",
            preview_template_branch="template-branch",
            preview_target_organisation="PREVIEW_TARGET_ORG",
            preview_target_repository="PREVIEW_TARGET_REPO",
            preview_target_branch=None,
            preview_target_namespace_template="my-app-${PREVIEW_ID_HASH}-preview",
            preview_target_max_namespace_length=50,
            replacements={
                "Chart.yaml": [GitOpsConfig.Replacement(path="name", value_template="${PREVIEW_NAMESPACE}")],
                "values.yaml": [
                    GitOpsConfig.Replacement(path="image.tag", value_template="${GIT_HASH}"),
                    GitOpsConfig.Replacement(path="route.host", value_template="${PREVIEW_HOST}"),
                ],
            },
        )

        self.template_git_repo_api_mock = self.create_mock(GitRepoApi)
        self.target_git_repo_api_mock = self.create_mock(GitRepoApi)

        self.git_repo_api_factory_mock = self.monkey_patch(GitRepoApiFactory)

        def git_repo_api_factory_create_mock(_: GitApiConfig, organisation: str, repository_name: str) -> GitRepoApi:
            if "TEMPLATE" in organisation and "TEMPLATE" in repository_name:
                return self.template_git_repo_api_mock
            if "TARGET" in organisation and "TARGET" in repository_name:
                return self.target_git_repo_api_mock
            raise Exception(f"no mock for {organisation}/{repository_name}")

        self.git_repo_api_factory_mock.create.side_effect = git_repo_api_factory_create_mock

        self.template_git_repo_mock = self.create_mock(GitRepo)
        self.template_git_repo_mock.__enter__.return_value = self.template_git_repo_mock
        self.template_git_repo_mock.__exit__.return_value = False
        self.template_git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/template-repo/{x}"
        self.template_git_repo_mock.clone.return_value = None
        self.template_git_repo_mock.commit.return_value = None
        self.template_git_repo_mock.push.return_value = None

        self.target_git_repo_mock = self.create_mock(GitRepo)
        self.target_git_repo_mock.__enter__.return_value = self.target_git_repo_mock
        self.target_git_repo_mock.__exit__.return_value = False
        self.target_git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/target-repo/{x}"
        self.target_git_repo_mock.clone.return_value = None

        def git_repo_constructor_mock(git_repo_api: GitRepoApi) -> GitRepo:
            if git_repo_api == self.template_git_repo_api_mock:
                return self.template_git_repo_mock
            if git_repo_api == self.target_git_repo_api_mock:
                return self.target_git_repo_mock
            raise Exception(f"no mock for {git_repo_api}")

        self.monkey_patch(GitRepo).side_effect = git_repo_constructor_mock

        self.seal_mocks()

    def test_create_new_preview(self):
        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/target-repo/my-app-685912d3-preview": False,  # doesn't exist yet -> expect create
            "/tmp/template-repo/.preview-templates/my-app": True,
        }[path]

        deployment_created_callback = Mock(return_value=None)

        command = CreatePreviewCommand(ARGS)
        command.register_callbacks(
            deployment_already_up_to_date_callback=lambda route_host: self.fail("should not be called"),
            deployment_updated_callback=lambda route_host: self.fail("should not be called"),
            deployment_created_callback=deployment_created_callback,
        )
        command.execute()

        deployment_created_callback.assert_called_once_with("created template 685912d3")

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO"),
            call.yaml_file_dump(
                {
                    "previewId": "PREVIEW_ID",
                    "previewIdHash": "685912d3",
                    "routeHost": "app.xy-685912d3.example.tld",
                    "namespace": "my-app-685912d3-preview",
                },
                "/tmp/gitopscli-preview-info.yaml",
            ),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.target_git_repo_api_mock),
            call.GitRepo.clone(None),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TEMPLATE_ORG", "PREVIEW_TEMPLATE_REPO"),
            call.GitRepo(self.template_git_repo_api_mock),
            call.GitRepo.clone("template-branch"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/target-repo/my-app-685912d3-preview"),
            call.logging.info("Create new folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/template-repo/.preview-templates/my-app"),
            call.logging.info("Using the preview template folder: %s", ".preview-templates/my-app"),
            call.shutil.copytree(
                "/tmp/template-repo/.preview-templates/my-app", "/tmp/target-repo/my-app-685912d3-preview"
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/Chart.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/Chart.yaml", "name", "my-app-685912d3-preview"
            ),
            call.logging.info(
                "Replaced property '%s' in '%s' with value: %s", "name", "Chart.yaml", "my-app-685912d3-preview"
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/values.yaml",
                "image.tag",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.logging.info(
                "Replaced property '%s' in '%s' with value: %s",
                "image.tag",
                "values.yaml",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/values.yaml", "route.host", "app.xy-685912d3.example.tld"
            ),
            call.logging.info(
                "Replaced property '%s' in '%s' with value: %s",
                "route.host",
                "values.yaml",
                "app.xy-685912d3.example.tld",
            ),
            call.GitRepo.commit(
                "GIT_USER",
                "GIT_EMAIL",
                "GIT_AUTHOR_NAME",
                "GIT_AUTHOR_EMAIL",
                "Create new preview environment for 'my-app' and git hash '3361723dbd91fcfae7b5b8b8b7d462fbc14187a9'.",
            ),
            call.GitRepo.push(),
        ]

    def test_create_new_preview_from_same_template_target_repo(self):
        gitops_config: GitOpsConfig = self.load_gitops_config_mock.return_value
        self.load_gitops_config_mock.return_value = GitOpsConfig(
            api_version=gitops_config.api_version,
            application_name=gitops_config.application_name,
            messages_created_template=gitops_config.messages_created_template,
            messages_updated_template=gitops_config.messages_updated_template,
            messages_uptodate_template=gitops_config.messages_uptodate_template,
            preview_host_template=gitops_config.preview_host_template,
            preview_template_organisation=gitops_config.preview_target_organisation,  # template = target
            preview_template_repository=gitops_config.preview_target_repository,  # template = target
            preview_template_path_template=gitops_config.preview_template_path_template,
            preview_template_branch=gitops_config.preview_target_branch,  # template = target
            preview_target_organisation=gitops_config.preview_target_organisation,
            preview_target_repository=gitops_config.preview_target_repository,
            preview_target_branch=gitops_config.preview_target_branch,
            preview_target_namespace_template=gitops_config.preview_target_namespace_template,
            preview_target_max_namespace_length=gitops_config.preview_target_max_namespace_length,
            replacements=gitops_config.replacements,
        )

        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/target-repo/my-app-685912d3-preview": False,  # doesn't exist yet -> expect create
            "/tmp/target-repo/.preview-templates/my-app": True,
        }[path]

        deployment_created_callback = Mock(return_value=None)

        command = CreatePreviewCommand(ARGS)
        command.register_callbacks(
            deployment_already_up_to_date_callback=lambda route_host: self.fail("should not be called"),
            deployment_updated_callback=lambda route_host: self.fail("should not be called"),
            deployment_created_callback=deployment_created_callback,
        )
        command.execute()

        deployment_created_callback.assert_called_once_with("created template 685912d3")

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO"),
            call.yaml_file_dump(
                {
                    "previewId": "PREVIEW_ID",
                    "previewIdHash": "685912d3",
                    "routeHost": "app.xy-685912d3.example.tld",
                    "namespace": "my-app-685912d3-preview",
                },
                "/tmp/gitopscli-preview-info.yaml",
            ),
            call.GitRepoApiFactory.create(
                ARGS, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"
            ),  # only clone once for template and target
            call.GitRepo(self.target_git_repo_api_mock),
            call.GitRepo.clone(None),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/target-repo/my-app-685912d3-preview"),
            call.logging.info("Create new folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/target-repo/.preview-templates/my-app"),
            call.logging.info("Using the preview template folder: %s", ".preview-templates/my-app"),
            call.shutil.copytree(
                "/tmp/target-repo/.preview-templates/my-app", "/tmp/target-repo/my-app-685912d3-preview"
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/Chart.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/Chart.yaml", "name", "my-app-685912d3-preview"
            ),
            call.logging.info(
                "Replaced property '%s' in '%s' with value: %s", "name", "Chart.yaml", "my-app-685912d3-preview"
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/values.yaml",
                "image.tag",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.logging.info(
                "Replaced property '%s' in '%s' with value: %s",
                "image.tag",
                "values.yaml",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/values.yaml", "route.host", "app.xy-685912d3.example.tld"
            ),
            call.logging.info(
                "Replaced property '%s' in '%s' with value: %s",
                "route.host",
                "values.yaml",
                "app.xy-685912d3.example.tld",
            ),
            call.GitRepo.commit(
                "GIT_USER",
                "GIT_EMAIL",
                "GIT_AUTHOR_NAME",
                "GIT_AUTHOR_EMAIL",
                "Create new preview environment for 'my-app' and git hash '3361723dbd91fcfae7b5b8b8b7d462fbc14187a9'.",
            ),
            call.GitRepo.push(),
        ]

    def test_update_existing_preview(self):
        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/target-repo/my-app-685912d3-preview": True,  # already exists -> expect update
        }[path]

        deployment_updated_callback = Mock(return_value=None)

        command = CreatePreviewCommand(ARGS)
        command.register_callbacks(
            deployment_already_up_to_date_callback=lambda route_host: self.fail("should not be called"),
            deployment_updated_callback=deployment_updated_callback,
            deployment_created_callback=lambda route_host: self.fail("should not be called"),
        )
        command.execute()

        deployment_updated_callback.assert_called_once_with("updated template 685912d3")

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO"),
            call.yaml_file_dump(INFO_YAML, "/tmp/gitopscli-preview-info.yaml"),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.target_git_repo_api_mock),
            call.GitRepo.clone(None),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TEMPLATE_ORG", "PREVIEW_TEMPLATE_REPO"),
            call.GitRepo(self.template_git_repo_api_mock),
            call.GitRepo.clone("template-branch"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/target-repo/my-app-685912d3-preview"),
            call.logging.info("Use existing folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/Chart.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/Chart.yaml", "name", "my-app-685912d3-preview"
            ),
            call.logging.info(
                "Replaced property '%s' in '%s' with value: %s", "name", "Chart.yaml", "my-app-685912d3-preview"
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/values.yaml",
                "image.tag",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.logging.info(
                "Replaced property '%s' in '%s' with value: %s",
                "image.tag",
                "values.yaml",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/values.yaml", "route.host", "app.xy-685912d3.example.tld"
            ),
            call.logging.info(
                "Replaced property '%s' in '%s' with value: %s",
                "route.host",
                "values.yaml",
                "app.xy-685912d3.example.tld",
            ),
            call.GitRepo.commit(
                "GIT_USER",
                "GIT_EMAIL",
                "GIT_AUTHOR_NAME",
                "GIT_AUTHOR_EMAIL",
                "Update preview environment for 'my-app' and git hash '3361723dbd91fcfae7b5b8b8b7d462fbc14187a9'.",
            ),
            call.GitRepo.push(),
        ]

    def test_preview_already_up_to_date(self):
        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/target-repo/my-app-685912d3-preview": True,  # already exists -> expect update
        }[path]

        self.update_yaml_file_mock.return_value = False  # nothing updated -> expect already up to date

        deployment_already_up_to_date_callback = Mock(return_value=None)

        command = CreatePreviewCommand(ARGS)
        command.register_callbacks(
            deployment_already_up_to_date_callback=deployment_already_up_to_date_callback,
            deployment_updated_callback=lambda route_host: self.fail("should not be called"),
            deployment_created_callback=lambda route_host: self.fail("should not be called"),
        )
        command.execute()

        deployment_already_up_to_date_callback.assert_called_once_with("uptodate template 685912d3")

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO"),
            call.yaml_file_dump(INFO_YAML, "/tmp/gitopscli-preview-info.yaml"),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.target_git_repo_api_mock),
            call.GitRepo.clone(None),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TEMPLATE_ORG", "PREVIEW_TEMPLATE_REPO"),
            call.GitRepo(self.template_git_repo_api_mock),
            call.GitRepo.clone("template-branch"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/target-repo/my-app-685912d3-preview"),
            call.logging.info("Use existing folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/Chart.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/Chart.yaml", "name", "my-app-685912d3-preview"
            ),
            call.logging.info("Keep property '%s' in '%s' value: %s", "name", "Chart.yaml", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/values.yaml",
                "image.tag",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.logging.info(
                "Keep property '%s' in '%s' value: %s",
                "image.tag",
                "values.yaml",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/values.yaml", "route.host", "app.xy-685912d3.example.tld"
            ),
            call.logging.info(
                "Keep property '%s' in '%s' value: %s", "route.host", "values.yaml", "app.xy-685912d3.example.tld"
            ),
            call.logging.info("The preview is already up-to-date. I'm done here."),
        ]

    def test_create_preview_for_unknown_template(self):
        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/target-repo/my-app-685912d3-preview": False,
            "/tmp/template-repo/.preview-templates/my-app": False,  # preview template missing -> expect error
        }[path]

        try:
            CreatePreviewCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("The preview template folder does not exist: .preview-templates/my-app", str(ex))

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO"),
            call.yaml_file_dump(INFO_YAML, "/tmp/gitopscli-preview-info.yaml"),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.target_git_repo_api_mock),
            call.GitRepo.clone(None),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TEMPLATE_ORG", "PREVIEW_TEMPLATE_REPO"),
            call.GitRepo(self.template_git_repo_api_mock),
            call.GitRepo.clone("template-branch"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/target-repo/my-app-685912d3-preview"),
            call.logging.info("Create new folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/template-repo/.preview-templates/my-app"),
        ]

    def test_create_preview_values_yaml_not_found(self):
        self.update_yaml_file_mock.side_effect = FileNotFoundError()

        try:
            CreatePreviewCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("No such file: my-app-685912d3-preview/Chart.yaml", str(ex))

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO"),
            call.yaml_file_dump(INFO_YAML, "/tmp/gitopscli-preview-info.yaml"),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.target_git_repo_api_mock),
            call.GitRepo.clone(None),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TEMPLATE_ORG", "PREVIEW_TEMPLATE_REPO"),
            call.GitRepo(self.template_git_repo_api_mock),
            call.GitRepo.clone("template-branch"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/target-repo/my-app-685912d3-preview"),
            call.logging.info("Use existing folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/Chart.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/Chart.yaml", "name", "my-app-685912d3-preview"
            ),
        ]

    def test_create_preview_values_yaml_parse_error(self):
        self.update_yaml_file_mock.side_effect = YAMLException()

        try:
            CreatePreviewCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("Error loading file: my-app-685912d3-preview/Chart.yaml", str(ex))

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO"),
            call.yaml_file_dump(INFO_YAML, "/tmp/gitopscli-preview-info.yaml"),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.target_git_repo_api_mock),
            call.GitRepo.clone(None),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TEMPLATE_ORG", "PREVIEW_TEMPLATE_REPO"),
            call.GitRepo(self.template_git_repo_api_mock),
            call.GitRepo.clone("template-branch"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/target-repo/my-app-685912d3-preview"),
            call.logging.info("Use existing folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/Chart.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/Chart.yaml", "name", "my-app-685912d3-preview"
            ),
        ]

    def test_create_preview_with_invalid_replacement_path(self):
        self.update_yaml_file_mock.side_effect = KeyError()

        try:
            CreatePreviewCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("Key 'name' not found in file: my-app-685912d3-preview/Chart.yaml", str(ex))

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO"),
            call.yaml_file_dump(INFO_YAML, "/tmp/gitopscli-preview-info.yaml"),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.target_git_repo_api_mock),
            call.GitRepo.clone(None),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TEMPLATE_ORG", "PREVIEW_TEMPLATE_REPO"),
            call.GitRepo(self.template_git_repo_api_mock),
            call.GitRepo.clone("template-branch"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/target-repo/my-app-685912d3-preview"),
            call.logging.info("Use existing folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/Chart.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/Chart.yaml", "name", "my-app-685912d3-preview"
            ),
        ]

    def test_create_new_preview_invalid_chart_template(self):
        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/target-repo/my-app-685912d3-preview": False,  # doesn't exist yet -> expect create
            "/tmp/template-repo/.preview-templates/my-app": True,
        }[path]

        self.update_yaml_file_mock.side_effect = KeyError()

        try:
            CreatePreviewCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("Key 'name' not found in file: my-app-685912d3-preview/Chart.yaml", str(ex))

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO"),
            call.yaml_file_dump(INFO_YAML, "/tmp/gitopscli-preview-info.yaml"),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TARGET_ORG", "PREVIEW_TARGET_REPO"),
            call.GitRepo(self.target_git_repo_api_mock),
            call.GitRepo.clone(None),
            call.GitRepoApiFactory.create(ARGS, "PREVIEW_TEMPLATE_ORG", "PREVIEW_TEMPLATE_REPO"),
            call.GitRepo(self.template_git_repo_api_mock),
            call.GitRepo.clone("template-branch"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/target-repo/my-app-685912d3-preview"),
            call.logging.info("Create new folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/template-repo/.preview-templates/my-app"),
            call.logging.info("Using the preview template folder: %s", ".preview-templates/my-app"),
            call.shutil.copytree(
                "/tmp/template-repo/.preview-templates/my-app", "/tmp/target-repo/my-app-685912d3-preview"
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/Chart.yaml"),
            call.update_yaml_file(
                "/tmp/target-repo/my-app-685912d3-preview/Chart.yaml", "name", "my-app-685912d3-preview"
            ),
        ]
