import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, Mock, call
import pytest
from gitopscli.git import GitApiConfig, GitRepoApi
from gitopscli.gitops_exception import GitOpsException
from gitopscli.commands.delete_preview import delete_preview_command, DeletePreviewArgs


class DeletePreviewCommandTest(unittest.TestCase):
    def setUp(self):
        def add_patch(target):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            return patcher.start()

        # Monkey patch all external functions the command is using:
        self.os_path_exists_mock = add_patch("gitopscli.commands.delete_preview.os.path.exists")
        self.shutil_rmtree_mock = add_patch("gitopscli.commands.delete_preview.shutil.rmtree")
        self.logging_mock = add_patch("gitopscli.commands.delete_preview.logging")
        self.load_gitops_config_mock = add_patch("gitopscli.commands.delete_preview.load_gitops_config")
        self.git_repo_api_factory_mock = add_patch("gitopscli.commands.delete_preview.GitRepoApiFactory")
        self.git_repo_mock = add_patch("gitopscli.commands.delete_preview.GitRepo")

        self.git_repo_api_mock = MagicMock()

        # Attach all mocks to a single mock manager
        self.mock_manager = Mock()
        self.mock_manager.attach_mock(self.git_repo_api_factory_mock, "GitRepoApiFactory")
        self.mock_manager.attach_mock(self.git_repo_api_mock, "GitRepoApi")
        self.mock_manager.attach_mock(self.git_repo_mock, "GitRepo")
        self.mock_manager.attach_mock(self.os_path_exists_mock, "os.path.exists")
        self.mock_manager.attach_mock(self.shutil_rmtree_mock, "shutil.rmtree")
        self.mock_manager.attach_mock(self.logging_mock, "logging")
        self.mock_manager.attach_mock(self.load_gitops_config_mock, "load_gitops_config")

        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock
        self.git_repo_api_mock.create_pull_request.return_value = GitRepoApi.PullRequestIdAndUrl(
            42, "<url of dummy pr>"
        )
        self.git_repo_mock.return_value = self.git_repo_mock
        self.git_repo_mock.__enter__.return_value = self.git_repo_mock
        self.git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/created-tmp-dir/{x}"
        self.os_path_exists_mock.return_value = True
        self.load_gitops_config_mock.return_value = SimpleNamespace(
            team_config_org="TEAM_CONFIG_ORG", team_config_repo="TEAM_CONFIG_REPO", application_name="APP"
        )

    def test_delete_existing_happy_flow(self):
        delete_preview_command(
            DeletePreviewArgs(
                username="USERNAME",
                password="PASSWORD",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                organisation="ORGA",
                repository_name="REPO",
                git_provider="github",
                git_provider_url=None,
                preview_id="PREVIEW_ID",
                expect_preview_exists=False,
            )
        )
        expected_git_api_config = GitApiConfig(
            username="USERNAME", password="PASSWORD", git_provider="github", git_provider_url=None,
        )
        assert self.mock_manager.method_calls == [
            call.load_gitops_config(expected_git_api_config, "ORGA", "REPO"),
            call.GitRepoApiFactory.create(expected_git_api_config, "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.logging.info("Preview folder name: %s", "APP-685912d3-preview"),
            call.GitRepo.get_full_file_path("APP-685912d3-preview"),
            call.os.path.exists("/tmp/created-tmp-dir/APP-685912d3-preview"),
            call.shutil.rmtree("/tmp/created-tmp-dir/APP-685912d3-preview", ignore_errors=True),
            call.GitRepo.commit(
                "GIT_USER", "GIT_EMAIL", "Delete preview environment for 'APP' and preview id 'PREVIEW_ID'."
            ),
            call.GitRepo.push("master"),
        ]

    def test_delete_missing_happy_flow(self):
        self.os_path_exists_mock.return_value = False

        delete_preview_command(
            DeletePreviewArgs(
                username="USERNAME",
                password="PASSWORD",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                organisation="ORGA",
                repository_name="REPO",
                git_provider="github",
                git_provider_url=None,
                preview_id="PREVIEW_ID",
                expect_preview_exists=False,
            )
        )
        expected_git_api_config = GitApiConfig(
            username="USERNAME", password="PASSWORD", git_provider="github", git_provider_url=None,
        )
        assert self.mock_manager.method_calls == [
            call.load_gitops_config(expected_git_api_config, "ORGA", "REPO"),
            call.GitRepoApiFactory.create(expected_git_api_config, "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.logging.info("Preview folder name: %s", "APP-685912d3-preview"),
            call.GitRepo.get_full_file_path("APP-685912d3-preview"),
            call.os.path.exists("/tmp/created-tmp-dir/APP-685912d3-preview"),
            call.logging.info(
                "No preview environment for '%s' and preview id '%s'. Nothing to do..", "APP", "PREVIEW_ID"
            ),
        ]

    def test_delete_missing_but_expected_error(self):
        self.os_path_exists_mock.return_value = False

        with pytest.raises(GitOpsException) as ex:
            delete_preview_command(
                DeletePreviewArgs(
                    username="USERNAME",
                    password="PASSWORD",
                    git_user="GIT_USER",
                    git_email="GIT_EMAIL",
                    organisation="ORGA",
                    repository_name="REPO",
                    git_provider="github",
                    git_provider_url=None,
                    preview_id="PREVIEW_ID",
                    expect_preview_exists=True,  # we expect an existing preview
                )
            )
        self.assertEqual(str(ex.value), "There was no preview with name: APP-685912d3-preview")

        expected_git_api_config = GitApiConfig(
            username="USERNAME", password="PASSWORD", git_provider="github", git_provider_url=None,
        )
        assert self.mock_manager.method_calls == [
            call.load_gitops_config(expected_git_api_config, "ORGA", "REPO"),
            call.GitRepoApiFactory.create(expected_git_api_config, "TEAM_CONFIG_ORG", "TEAM_CONFIG_REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.checkout("master"),
            call.logging.info("Preview folder name: %s", "APP-685912d3-preview"),
            call.GitRepo.get_full_file_path("APP-685912d3-preview"),
            call.os.path.exists("/tmp/created-tmp-dir/APP-685912d3-preview"),
        ]

    def test_missing_gitops_config_yaml_error(self):
        self.load_gitops_config_mock.side_effect = GitOpsException()

        with pytest.raises(GitOpsException):
            delete_preview_command(
                DeletePreviewArgs(
                    username="USERNAME",
                    password="PASSWORD",
                    git_user="GIT_USER",
                    git_email="GIT_EMAIL",
                    organisation="ORGA",
                    repository_name="REPO",
                    git_provider="github",
                    git_provider_url=None,
                    preview_id="PREVIEW_ID",
                    expect_preview_exists=True,  # we expect an existing preview
                )
            )
        expected_git_api_config = GitApiConfig(
            username="USERNAME", password="PASSWORD", git_provider="github", git_provider_url=None,
        )
        assert self.mock_manager.method_calls == [
            call.load_gitops_config(expected_git_api_config, "ORGA", "REPO"),
        ]
