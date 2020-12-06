import os
import unittest
import shutil
import logging
from unittest.mock import call, Mock
from gitopscli.io.yaml_util import update_yaml_file
from gitopscli.git import GitRepo, GitRepoApi, GitRepoApiFactory, GitProvider
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
    organisation="ORGA",
    repository_name="REPO",
    git_provider=GitProvider.GITHUB,
    git_provider_url=None,
    preview_id="PREVIEW_ID",
    git_hash=DUMMY_GIT_HASH,
)


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

        self.load_gitops_config_mock = self.monkey_patch(load_gitops_config)
        self.load_gitops_config_mock.return_value = GitOpsConfig(
            team_config_org="TEAM_CONFIG_ORG",
            team_config_repo="TEAM_CONFIG_REPO",
            application_name="my-app",
            route_host="app.xy-{SHA256_8CHAR_BRANCH_HASH}.example.tld",
            replacements=[
                GitOpsConfig.Replacement(path="image.tag", variable="GIT_COMMIT"),
                GitOpsConfig.Replacement(path="route.host", variable="ROUTE_HOST"),
            ],
        )

        self.git_repo_api_mock = self.create_mock(GitRepoApi)

        self.git_repo_api_factory_mock = self.monkey_patch(GitRepoApiFactory)
        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock

        self.git_repo_mock = self.monkey_patch(GitRepo)
        self.git_repo_mock.return_value = self.git_repo_mock
        self.git_repo_mock.__enter__.return_value = self.git_repo_mock
        self.git_repo_mock.__exit__.return_value = False
        self.git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/created-tmp-dir/{x}"
        self.git_repo_mock.checkout.return_value = None
        self.git_repo_mock.commit.return_value = None
        self.git_repo_mock.push.return_value = None

        self.seal_mocks()

    def test_create_new_preview(self):
        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/created-tmp-dir/.preview-templates/my-app": True,
            "/tmp/created-tmp-dir/my-app-685912d3-preview": False,  # doesn't exist yet -> expect create
        }[path]

        deployment_created_callback = Mock(return_value=None)

        command = CreatePreviewCommand(ARGS)
        command.register_callbacks(
            deployment_already_up_to_date_callback=lambda route_host: self.fail("should not be called"),
            deployment_updated_callback=lambda route_host: self.fail("should not be called"),
            deployment_created_callback=deployment_created_callback,
        )
        command.execute()

        deployment_created_callback.assert_called_once_with("app.xy-685912d3.example.tld")

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO",),
            call.GitRepoApiFactory.create(ARGS, "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO",),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/created-tmp-dir/.preview-templates/my-app"),
            call.logging.info("Using the preview template folder: %s", ".preview-templates/my-app"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/created-tmp-dir/my-app-685912d3-preview"),
            call.logging.info("Create new folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.shutil.copytree(
                "/tmp/created-tmp-dir/.preview-templates/my-app", "/tmp/created-tmp-dir/my-app-685912d3-preview"
            ),
            call.logging.info("Looking for Chart.yaml at: %s", "my-app-685912d3-preview/Chart.yaml"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/Chart.yaml"),
            call.update_yaml_file(
                "/tmp/created-tmp-dir/my-app-685912d3-preview/Chart.yaml", "name", "my-app-685912d3-preview"
            ),
            call.logging.info("Using image tag from git hash: %s", "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/created-tmp-dir/my-app-685912d3-preview/values.yaml",
                "image.tag",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.logging.info(
                "Replaced property %s with value: %s", "image.tag", "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9"
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/created-tmp-dir/my-app-685912d3-preview/values.yaml", "route.host", "app.xy-685912d3.example.tld"
            ),
            call.logging.info("Replaced property %s with value: %s", "route.host", "app.xy-685912d3.example.tld"),
            call.GitRepo.commit(
                "GIT_USER",
                "GIT_EMAIL",
                "Create new preview environment for 'my-app' and git hash '3361723dbd91fcfae7b5b8b8b7d462fbc14187a9'.",
            ),
            call.GitRepo.push("master"),
        ]

    def test_update_existing_preview(self):
        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/created-tmp-dir/.preview-templates/my-app": True,
            "/tmp/created-tmp-dir/my-app-685912d3-preview": True,  # already exists -> expect update
        }[path]

        deployment_updated_callback = Mock(return_value=None)

        command = CreatePreviewCommand(ARGS)
        command.register_callbacks(
            deployment_already_up_to_date_callback=lambda route_host: self.fail("should not be called"),
            deployment_updated_callback=deployment_updated_callback,
            deployment_created_callback=lambda route_host: self.fail("should not be called"),
        )
        command.execute()

        deployment_updated_callback.assert_called_once_with("app.xy-685912d3.example.tld")

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO",),
            call.GitRepoApiFactory.create(ARGS, "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO",),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/created-tmp-dir/.preview-templates/my-app"),
            call.logging.info("Using the preview template folder: %s", ".preview-templates/my-app"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/created-tmp-dir/my-app-685912d3-preview"),
            call.logging.info("Use existing folder for preview: %s", "my-app-685912d3-preview"),
            call.logging.info("Using image tag from git hash: %s", "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/created-tmp-dir/my-app-685912d3-preview/values.yaml",
                "image.tag",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.logging.info(
                "Replaced property %s with value: %s", "image.tag", "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9"
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/created-tmp-dir/my-app-685912d3-preview/values.yaml", "route.host", "app.xy-685912d3.example.tld"
            ),
            call.logging.info("Replaced property %s with value: %s", "route.host", "app.xy-685912d3.example.tld"),
            call.GitRepo.commit(
                "GIT_USER",
                "GIT_EMAIL",
                "Update preview environment for 'my-app' and git hash '3361723dbd91fcfae7b5b8b8b7d462fbc14187a9'.",
            ),
            call.GitRepo.push("master"),
        ]

    def test_preview_already_up_to_date(self):
        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/created-tmp-dir/.preview-templates/my-app": True,
            "/tmp/created-tmp-dir/my-app-685912d3-preview": True,  # already exists -> expect update
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

        deployment_already_up_to_date_callback.assert_called_once_with("app.xy-685912d3.example.tld")

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO",),
            call.GitRepoApiFactory.create(ARGS, "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO",),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/created-tmp-dir/.preview-templates/my-app"),
            call.logging.info("Using the preview template folder: %s", ".preview-templates/my-app"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/created-tmp-dir/my-app-685912d3-preview"),
            call.logging.info("Use existing folder for preview: %s", "my-app-685912d3-preview"),
            call.logging.info("Using image tag from git hash: %s", "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/created-tmp-dir/my-app-685912d3-preview/values.yaml",
                "image.tag",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/created-tmp-dir/my-app-685912d3-preview/values.yaml", "route.host", "app.xy-685912d3.example.tld"
            ),
            call.logging.info(
                "The image tag %s has already been deployed. Doing nothing.", "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9"
            ),
        ]

    def test_create_preview_for_unknown_template(self):
        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/created-tmp-dir/.preview-templates/my-app": False,  # preview template missing -> expect error
        }[path]

        try:
            CreatePreviewCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("The preview template folder does not exist: .preview-templates/my-app", str(ex))

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO",),
            call.GitRepoApiFactory.create(ARGS, "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO",),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/created-tmp-dir/.preview-templates/my-app"),
        ]

    def test_create_preview_with_unknown_replacement_variable(self):
        self.load_gitops_config_mock.return_value = GitOpsConfig(
            team_config_org="TEAM_CONFIG_ORG",
            team_config_repo="TEAM_CONFIG_REPO",
            application_name="my-app",
            route_host="app.xy-{SHA256_8CHAR_BRANCH_HASH}.example.tld",
            replacements=[GitOpsConfig.Replacement(path="image.tag", variable="UNKNOWN"),],  # this should fail
        )

        try:
            CreatePreviewCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("Unknown replacement variable for 'image.tag': UNKNOWN", str(ex))

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO",),
            call.GitRepoApiFactory.create(ARGS, "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO",),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/created-tmp-dir/.preview-templates/my-app"),
            call.logging.info("Using the preview template folder: %s", ".preview-templates/my-app"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/created-tmp-dir/my-app-685912d3-preview"),
            call.logging.info("Use existing folder for preview: %s", "my-app-685912d3-preview"),
            call.logging.info("Using image tag from git hash: %s", "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9"),
        ]

    def test_create_preview_with_invalid_replacement_path(self):
        self.update_yaml_file_mock.side_effect = KeyError()

        try:
            CreatePreviewCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("Key 'image.tag' not found in 'my-app-685912d3-preview/values.yaml'", str(ex))

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO",),
            call.GitRepoApiFactory.create(ARGS, "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO",),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/created-tmp-dir/.preview-templates/my-app"),
            call.logging.info("Using the preview template folder: %s", ".preview-templates/my-app"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/created-tmp-dir/my-app-685912d3-preview"),
            call.logging.info("Use existing folder for preview: %s", "my-app-685912d3-preview"),
            call.logging.info("Using image tag from git hash: %s", "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/values.yaml"),
            call.update_yaml_file(
                "/tmp/created-tmp-dir/my-app-685912d3-preview/values.yaml",
                "image.tag",
                "3361723dbd91fcfae7b5b8b8b7d462fbc14187a9",
            ),
        ]

    def test_create_new_preview_invalid_chart_template(self):
        self.os_mock.path.isdir.side_effect = lambda path: {
            "/tmp/created-tmp-dir/.preview-templates/my-app": True,
            "/tmp/created-tmp-dir/my-app-685912d3-preview": False,  # doesn't exist yet -> expect create
        }[path]

        self.update_yaml_file_mock.side_effect = KeyError()

        try:
            CreatePreviewCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("Key 'name' not found in 'my-app-685912d3-preview/Chart.yaml'", str(ex))

        assert self.mock_manager.method_calls == [
            call.load_gitops_config(ARGS, "ORGA", "REPO",),
            call.GitRepoApiFactory.create(ARGS, "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO",),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.os.path.isdir("/tmp/created-tmp-dir/.preview-templates/my-app"),
            call.logging.info("Using the preview template folder: %s", ".preview-templates/my-app"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.os.path.isdir("/tmp/created-tmp-dir/my-app-685912d3-preview"),
            call.logging.info("Create new folder for preview: %s", "my-app-685912d3-preview"),
            call.GitRepo.get_full_file_path(".preview-templates/my-app"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview"),
            call.shutil.copytree(
                "/tmp/created-tmp-dir/.preview-templates/my-app", "/tmp/created-tmp-dir/my-app-685912d3-preview"
            ),
            call.logging.info("Looking for Chart.yaml at: %s", "my-app-685912d3-preview/Chart.yaml"),
            call.GitRepo.get_full_file_path("my-app-685912d3-preview/Chart.yaml"),
            call.update_yaml_file(
                "/tmp/created-tmp-dir/my-app-685912d3-preview/Chart.yaml", "name", "my-app-685912d3-preview"
            ),
        ]
