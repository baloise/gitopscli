import unittest
from unittest.mock import call
import pytest
from gitopscli.gitops_exception import GitOpsException
from gitopscli.gitops_config import GitOpsConfig
from gitopscli.io.yaml_util import yaml_file_load
from gitopscli.git import GitApiConfig, GitProvider, GitRepo, GitRepoApi, GitRepoApiFactory
from gitopscli.commands.common.gitops_config_loader import load_gitops_config
from tests.commands.mock_mixin import MockMixin


class GitOpsConfigLoaderTest(MockMixin, unittest.TestCase):
    git_api_config = GitApiConfig(
        username="USERNAME", password="PASSWORD", git_provider=GitProvider.GITHUB, git_provider_url=None,
    )

    def setUp(self):
        self.init_mock_manager(load_gitops_config)

        self.gitops_config_mock = self.monkey_patch(GitOpsConfig)
        self.gitops_config_mock.from_yaml.return_value = self.gitops_config_mock

        self.yaml_file_load_mock = self.monkey_patch(yaml_file_load)
        self.yaml_file_load_mock.return_value = {"dummy": "gitopsconfig"}

        self.git_repo_api_mock = self.create_mock(GitRepoApi)

        self.git_repo_api_factory_mock = self.monkey_patch(GitRepoApiFactory)
        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock

        self.git_repo_mock = self.monkey_patch(GitRepo)
        self.git_repo_mock.return_value = self.git_repo_mock
        self.git_repo_mock.__enter__.return_value = self.git_repo_mock
        self.git_repo_mock.__exit__.return_value = False
        self.git_repo_mock.clone.return_value = None
        self.git_repo_mock.get_full_file_path.side_effect = lambda x: f"/repo-dir/{x}"

        self.seal_mocks()

    def test_happy_flow(self):
        gitops_config = load_gitops_config(
            git_api_config=self.git_api_config, organisation="ORGA", repository_name="REPO"
        )

        assert gitops_config == self.gitops_config_mock

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self.git_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.clone(),
            call.GitRepo.get_full_file_path(".gitops.config.yaml"),
            call.yaml_file_load("/repo-dir/.gitops.config.yaml"),
            call.GitOpsConfig.from_yaml({"dummy": "gitopsconfig"}),
        ]

    def test_file_not_found(self):
        self.yaml_file_load_mock.side_effect = FileNotFoundError("file not found")

        with pytest.raises(GitOpsException) as ex:
            load_gitops_config(git_api_config=self.git_api_config, organisation="ORGA", repository_name="REPO")

        self.assertEqual(str(ex.value), "No such file: .gitops.config.yaml")

        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(self.git_api_config, "ORGA", "REPO"),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.clone(),
            call.GitRepo.get_full_file_path(".gitops.config.yaml"),
            call.yaml_file_load("/repo-dir/.gitops.config.yaml"),
        ]
