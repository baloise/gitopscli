import unittest
from unittest.mock import patch, MagicMock, Mock, call
from gitopscli.git import GitApiConfig, GitProvider
from gitopscli.commands.sync_apps import SyncAppsCommand


class SyncAppsCommandTest(unittest.TestCase):
    def setUp(self):
        def add_patch(target):
            patcher = patch(target)
            self.addCleanup(patcher.stop)
            return patcher.start()

        # Monkey patch all external functions the command is using:
        self.os_path_exists_mock = add_patch("gitopscli.commands.sync_apps.os.path.exists")
        self.os_path_isdir_mock = add_patch("gitopscli.commands.sync_apps.os.path.isdir")
        self.os_listdir_mock = add_patch("gitopscli.commands.sync_apps.os.listdir")
        self.logging_mock = add_patch("gitopscli.commands.sync_apps.logging")
        self.git_repo_api_factory_mock = add_patch("gitopscli.commands.sync_apps.GitRepoApiFactory")
        self.git_repo_mock = add_patch("gitopscli.commands.sync_apps.GitRepo")
        self.open_mock = add_patch("gitopscli.commands.sync_apps.open")
        self.yaml_factory_mock = add_patch("gitopscli.commands.sync_apps.YAML")
        self.merge_yaml_element_mock = add_patch("gitopscli.commands.sync_apps.merge_yaml_element")

        self.team_config_git_repo_api_mock = MagicMock()
        self.root_config_git_repo_api_mock = MagicMock()

        self.team_config_git_repo_mock = MagicMock()
        self.root_config_git_repo_mock = MagicMock()

        self.yaml_mock = MagicMock()

        # Attach all mocks to a single mock manager
        self.mock_manager = Mock()
        self.mock_manager.attach_mock(self.git_repo_api_factory_mock, "GitRepoApiFactory")
        self.mock_manager.attach_mock(self.git_repo_mock, "GitRepo")
        self.mock_manager.attach_mock(self.team_config_git_repo_mock, "GitRepo_team")
        self.mock_manager.attach_mock(self.root_config_git_repo_mock, "GitRepo_root")
        self.mock_manager.attach_mock(self.os_path_exists_mock, "os.path.exists")
        self.mock_manager.attach_mock(self.os_path_isdir_mock, "os.path.isdir")
        self.mock_manager.attach_mock(self.os_listdir_mock, "os.listdir")
        self.mock_manager.attach_mock(self.logging_mock, "logging")
        self.mock_manager.attach_mock(self.open_mock, "open")
        self.mock_manager.attach_mock(self.yaml_mock, "YAML")
        self.mock_manager.attach_mock(self.merge_yaml_element_mock, "merge_yaml_element")

        # let GitRepoApiFactory.create() return a different GitRepoApi mock depending on provided repo name
        self.git_repo_api_factory_mock.create.side_effect = lambda config, org, repo: (
            self.team_config_git_repo_api_mock if repo == "REPO" else self.root_config_git_repo_api_mock
        )

        # let GitRepo's constructor return a different mock depending on provided GitRepoApi
        self.git_repo_mock.side_effect = lambda api: (
            self.team_config_git_repo_mock
            if api is self.team_config_git_repo_api_mock
            else self.root_config_git_repo_mock
        )

        self.team_config_git_repo_mock.__enter__.return_value = self.team_config_git_repo_mock
        self.team_config_git_repo_mock.get_clone_url.return_value = "https://team.config.repo.git"
        self.team_config_git_repo_mock.get_author_from_last_commit.return_value = "author"

        self.root_config_git_repo_mock.__enter__.return_value = self.root_config_git_repo_mock
        self.root_config_git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/created-tmp-dir/{x}"
        self.root_config_git_repo_mock.get_clone_url.return_value = "https://root.config.repo.git"

        self.os_path_exists_mock.return_value = True
        self.os_path_isdir_mock.return_value = True

        self.open_mock.return_value = self.open_mock
        self.open_mock.__enter__.return_value = self.open_mock

        self.os_listdir_mock.return_value = ["folder"]

        self.yaml_factory_mock.return_value = self.yaml_mock

        bootstrap_values_content = {
            "bootstrap": [{"name": "team-non-prod"}],
            "repository": "https://root.config.repo.git",
        }
        apps_team_content = {"teamName": "team1", "repository": "https://team.config.repo.git"}
        self.yaml_mock.load.side_effect = [bootstrap_values_content, apps_team_content]

    def test_sync_apps_happy_flow(self):
        SyncAppsCommand(
            SyncAppsCommand.Args(
                username="USERNAME",
                password="PASSWORD",
                git_user="GIT_USER",
                git_email="GIT_EMAIL",
                root_organisation="ROOT_ORGA",
                root_repository_name="ROOT_REPO",
                organisation="ORGA",
                repository_name="REPO",
                git_provider=GitProvider.GITHUB,
                git_provider_url=None,
            )
        ).execute()
        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(
                GitApiConfig(
                    username="USERNAME", password="PASSWORD", git_provider=GitProvider.GITHUB, git_provider_url=None
                ),
                "ORGA",
                "REPO",
            ),
            call.GitRepoApiFactory.create(
                GitApiConfig(
                    username="USERNAME", password="PASSWORD", git_provider=GitProvider.GITHUB, git_provider_url=None
                ),
                "ROOT_ORGA",
                "ROOT_REPO",
            ),
            call.GitRepo(self.team_config_git_repo_api_mock),
            call.GitRepo(self.root_config_git_repo_api_mock),
            call.GitRepo_team.get_clone_url(),
            call.logging.info("Team config repository: %s", "https://team.config.repo.git"),
            call.GitRepo_root.get_clone_url(),
            call.logging.info("Root config repository: %s", "https://root.config.repo.git"),
            call.GitRepo_root.checkout("master"),
            call.GitRepo_root.get_full_file_path("."),
            call.os.listdir("/tmp/created-tmp-dir/."),
            call.os.path.isdir("/tmp/created-tmp-dir/./folder"),
            call.logging.info("Found %s app(s) in apps repository: %s", 1, "folder"),
            call.logging.info("Searching apps repository in root repository's 'apps/' directory..."),
            call.GitRepo_root.checkout("master"),
            call.GitRepo_root.get_full_file_path("bootstrap/values.yaml"),
            call.open("/tmp/created-tmp-dir/bootstrap/values.yaml", "r"),
            call.YAML.load(self.open_mock),
            call.logging.info("Analyzing %s in root repository", "apps/team-non-prod.yaml"),
            call.GitRepo_root.get_full_file_path("apps/team-non-prod.yaml"),
            call.open("/tmp/created-tmp-dir/apps/team-non-prod.yaml", "r"),
            call.YAML.load(self.open_mock),
            call.GitRepo_team.get_clone_url(),
            call.logging.info("Found apps repository in %s", "apps/team-non-prod.yaml"),
            call.logging.info("Sync applications in root repository's %s.", "apps/team-non-prod.yaml"),
            call.merge_yaml_element("/tmp/created-tmp-dir/apps/team-non-prod.yaml", "applications", {"folder": {}}),
            call.GitRepo_team.get_author_from_last_commit(),
            call.GitRepo_root.commit("GIT_USER", "GIT_EMAIL", "author updated apps/team-non-prod.yaml"),
            call.GitRepo_root.push("master"),
        ]
