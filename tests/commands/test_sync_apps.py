import logging
import os
import unittest
from unittest.mock import call
from gitopscli.git import GitProvider, GitRepo, GitRepoApi, GitRepoApiFactory
from gitopscli.commands.sync_apps import SyncAppsCommand
from gitopscli.io.yaml_util import merge_yaml_element, yaml_file_load
from .mock_mixin import MockMixin


class SyncAppsCommandTest(MockMixin, unittest.TestCase):
    def setUp(self):
        self.init_mock_manager(SyncAppsCommand)

        self.os_mock = self.monkey_patch(os)
        self.os_mock.path.isdir.return_value = True
        self.os_mock.path.join.side_effect = os.path.join
        self.os_mock.listdir.return_value = ["folder"]

        self.logging_mock = self.monkey_patch(logging)
        self.logging_mock.info.return_value = None

        self.team_config_git_repo_api_mock = self.create_mock(GitRepoApi)
        self.root_config_git_repo_api_mock = self.create_mock(GitRepoApi)

        self.team_config_git_repo_mock = self.create_mock(GitRepo, "GitRepo_team")
        self.team_config_git_repo_mock.__enter__.return_value = self.team_config_git_repo_mock
        self.team_config_git_repo_mock.__exit__.return_value = False
        self.team_config_git_repo_mock.get_clone_url.return_value = "https://team.config.repo.git"
        self.team_config_git_repo_mock.checkout.return_value = None
        self.team_config_git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/team-config-repo/{x}"
        self.team_config_git_repo_mock.get_author_from_last_commit.return_value = "author"

        self.root_config_git_repo_mock = self.create_mock(GitRepo, "GitRepo_root")
        self.root_config_git_repo_mock.__enter__.return_value = self.root_config_git_repo_mock
        self.root_config_git_repo_mock.__exit__.return_value = False
        self.root_config_git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/root-config-repo/{x}"
        self.root_config_git_repo_mock.get_clone_url.return_value = "https://root.config.repo.git"
        self.root_config_git_repo_mock.checkout.return_value = None
        self.root_config_git_repo_mock.commit.return_value = None
        self.root_config_git_repo_mock.push.return_value = None

        self.git_repo_api_factory_mock = self.monkey_patch(GitRepoApiFactory)
        self.git_repo_api_factory_mock.create.side_effect = lambda config, org, repo: {
            ("TEAM_ORGA", "TEAM_REPO"): self.team_config_git_repo_api_mock,
            ("ROOT_ORGA", "ROOT_REPO"): self.root_config_git_repo_api_mock,
        }[(org, repo)]

        self.git_repo_mock = self.monkey_patch(GitRepo)
        self.git_repo_mock.side_effect = lambda api: {
            id(self.team_config_git_repo_api_mock): self.team_config_git_repo_mock,
            id(self.root_config_git_repo_api_mock): self.root_config_git_repo_mock,
        }[id(api)]

        self.yaml_file_load_mock = self.monkey_patch(yaml_file_load)
        bootstrap_values_content = {
            "bootstrap": [{"name": "team-non-prod"}],
            "repository": "https://root.config.repo.git",
        }
        apps_team_content = {"teamName": "team1", "repository": "https://team.config.repo.git"}
        self.yaml_file_load_mock.side_effect = [bootstrap_values_content, apps_team_content]

        self.merge_yaml_element_mock = self.monkey_patch(merge_yaml_element)
        self.merge_yaml_element_mock.return_value = None

        self.seal_mocks()

    def test_sync_apps_happy_flow(self):
        args = SyncAppsCommand.Args(
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            root_organisation="ROOT_ORGA",
            root_repository_name="ROOT_REPO",
            organisation="TEAM_ORGA",
            repository_name="TEAM_REPO",
            git_provider=GitProvider.GITHUB,
            git_provider_url=None,
        )
        SyncAppsCommand(args).execute()
        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(args, "TEAM_ORGA", "TEAM_REPO",),
            call.GitRepoApiFactory.create(args, "ROOT_ORGA", "ROOT_REPO",),
            call.GitRepo(self.team_config_git_repo_api_mock),
            call.GitRepo(self.root_config_git_repo_api_mock),
            call.GitRepo_team.get_clone_url(),
            call.logging.info("Team config repository: %s", "https://team.config.repo.git"),
            call.GitRepo_root.get_clone_url(),
            call.logging.info("Root config repository: %s", "https://root.config.repo.git"),
            call.GitRepo_team.checkout("master"),
            call.GitRepo_team.get_full_file_path("."),
            call.os.listdir("/tmp/team-config-repo/."),
            call.os.path.join("/tmp/team-config-repo/.", "folder"),
            call.os.path.isdir("/tmp/team-config-repo/./folder"),
            call.logging.info("Found %s app(s) in apps repository: %s", 1, "folder"),
            call.logging.info("Searching apps repository in root repository's 'apps/' directory..."),
            call.GitRepo_root.checkout("master"),
            call.GitRepo_root.get_full_file_path("bootstrap/values.yaml"),
            call.yaml_file_load("/tmp/root-config-repo/bootstrap/values.yaml"),
            call.logging.info("Analyzing %s in root repository", "apps/team-non-prod.yaml"),
            call.GitRepo_root.get_full_file_path("apps/team-non-prod.yaml"),
            call.yaml_file_load("/tmp/root-config-repo/apps/team-non-prod.yaml"),
            call.GitRepo_team.get_clone_url(),
            call.logging.info("Found apps repository in %s", "apps/team-non-prod.yaml"),
            call.logging.info("Sync applications in root repository's %s.", "apps/team-non-prod.yaml"),
            call.merge_yaml_element("/tmp/root-config-repo/apps/team-non-prod.yaml", "applications", {"folder": {}}),
            call.GitRepo_team.get_author_from_last_commit(),
            call.GitRepo_root.commit("GIT_USER", "GIT_EMAIL", "author updated apps/team-non-prod.yaml"),
            call.GitRepo_root.push("master"),
        ]
