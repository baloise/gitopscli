import unittest
from unittest.mock import patch, MagicMock, Mock, call
import pytest
from gitopscli.gitops_exception import GitOpsException
from gitopscli.git import GitApiConfig
from gitopscli.commands.common import load_gitops_config


class GitOpsConfigLoaderTest(unittest.TestCase):
    git_api_config = GitApiConfig(
        username="USERNAME", password="PASSWORD", git_provider="github", git_provider_url=None,
    )

    def setUp(self):
        def add_patch(target):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            return patcher.start()

        # Monkey patch all external functions the command is using:
        self.logging_mock = add_patch("gitopscli.commands.common.gitops_config_loader.logging")
        self.gitops_config_mock = add_patch("gitopscli.commands.common.gitops_config_loader.GitOpsConfig")
        self.git_repo_api_factory_mock = add_patch("gitopscli.commands.common.gitops_config_loader.GitRepoApiFactory")
        self.git_repo_mock = add_patch("gitopscli.commands.common.gitops_config_loader.GitRepo")
        self.git_repo_api_mock = MagicMock()

        # Attach all mocks to a single mock manager
        self.mock_manager = Mock()
        self.mock_manager.attach_mock(self.git_repo_api_factory_mock, "GitRepoApiFactory")
        self.mock_manager.attach_mock(self.git_repo_api_mock, "GitRepoApi")
        self.mock_manager.attach_mock(self.git_repo_mock, "GitRepo")
        self.mock_manager.attach_mock(self.logging_mock, "logging")
        self.mock_manager.attach_mock(self.gitops_config_mock, "GitOpsConfig")

        # Define some common default return values
        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock
        self.git_repo_mock.return_value = self.git_repo_mock
        self.git_repo_mock.__enter__.return_value = self.git_repo_mock
        self.git_repo_mock.get_full_file_path.side_effect = lambda x: f"/repo-dir/{x}"
        self.gitops_config_mock.return_value = self.gitops_config_mock

    def test_happy_flow(self):
        gitops_config = load_gitops_config(
            git_api_config=self.git_api_config, organisation="ORGA", repository_name="REPO"
        )

        assert gitops_config == self.gitops_config_mock

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self.git_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.logging.info("Checkout '%s/%s' branch 'master'...", "ORGA", "REPO"),
            call.GitRepo.checkout("master"),
            call.logging.info("Reading '.gitops.config.yaml'..."),
            call.GitRepo.get_full_file_path(".gitops.config.yaml"),
            call.GitOpsConfig("/repo-dir/.gitops.config.yaml"),
        ]

    def test_file_not_found(self):
        self.gitops_config_mock.side_effect = FileNotFoundError("file not found")

        with pytest.raises(GitOpsException) as ex:
            load_gitops_config(git_api_config=self.git_api_config, organisation="ORGA", repository_name="REPO")

        self.assertEqual(str(ex.value), "No such file: .gitops.config.yaml")

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self.git_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.logging.info("Checkout '%s/%s' branch 'master'...", "ORGA", "REPO"),
            call.GitRepo.checkout("master"),
            call.logging.info("Reading '.gitops.config.yaml'..."),
            call.GitRepo.get_full_file_path(".gitops.config.yaml"),
            call.GitOpsConfig("/repo-dir/.gitops.config.yaml"),
        ]
