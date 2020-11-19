import unittest
from unittest.mock import patch, MagicMock, Mock, call
from gitopscli.git import GitApiConfig, GitRepoApi
from gitopscli.commands.sync_apps import sync_apps_command


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

        self.git_repo_api_mock = MagicMock()
        self.yaml_mock = MagicMock()

        # Attach all mocks to a single mock manager
        self.mock_manager = Mock()
        self.mock_manager.attach_mock(self.git_repo_api_factory_mock, "GitRepoApiFactory")
        self.mock_manager.attach_mock(self.git_repo_api_mock, "GitRepoApi")
        self.mock_manager.attach_mock(self.git_repo_mock, "GitRepo")
        self.mock_manager.attach_mock(self.os_path_exists_mock, "os.path.exists")
        self.mock_manager.attach_mock(self.os_path_isdir_mock, "os.path.isdir")
        self.mock_manager.attach_mock(self.os_listdir_mock, "os.listdir")
        self.mock_manager.attach_mock(self.logging_mock, "logging")
        self.mock_manager.attach_mock(self.open_mock, "open")
        self.mock_manager.attach_mock(self.yaml_mock, "YAML")
        self.mock_manager.attach_mock(self.merge_yaml_element_mock, "merge_yaml_element")

        self.git_repo_api_factory_mock.create.return_value = self.git_repo_api_mock
        self.yaml_factory_mock.return_value = self.yaml_mock
        self.git_repo_api_mock.create_pull_request.return_value = GitRepoApi.PullRequestIdAndUrl(
            "<dummy pr id>", "<url of dummy pr>"
        )
        self.git_repo_mock.return_value = self.git_repo_mock
        self.git_repo_mock.__enter__.return_value = self.git_repo_mock
        self.git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/created-tmp-dir/{x}"
        self.git_repo_mock.get_clone_url.return_value = "somerepo"
        self.git_repo_mock.get_author_from_last_commit.return_value = "author"
        self.os_path_exists_mock.return_value = True
        self.os_path_isdir_mock.return_value = True
        self.open_mock.return_value = self.open_mock
        self.open_mock.__enter__.return_value = self.open_mock
        self.os_listdir_mock.return_value = ['folder']
        bootstrap_values_content = {"bootstrap": [{"name": "team-non-prod"}], "repository": "somerepo"}
        apps_team_content = {"teamName": "team1", "repository": "somerepo"}
        self.yaml_mock.load.side_effect = [bootstrap_values_content, apps_team_content]

    def test_sync_apps_happy_flow(self):
        sync_apps_command(
            command="sync-apps",
            username="USERNAME",
            password="PASSWORD",
            git_user="GIT_USER",
            git_email="GIT_EMAIL",
            root_organisation="ROOT_ORGA",
            root_repository_name="ROOT_REPO",
            organisation="ORGA",
            repository_name="REPO",
            git_provider="github",
            git_provider_url=None,
        )
        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(GitApiConfig(username='USERNAME', password='PASSWORD', git_provider='github', git_provider_url=None), 'ORGA', 'REPO'),
            call.GitRepoApiFactory.create(GitApiConfig(username='USERNAME', password='PASSWORD', git_provider='github', git_provider_url=None), 'ROOT_ORGA', 'ROOT_REPO'),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo(self.git_repo_api_mock),
            call.GitRepo.get_clone_url(),
            call.logging.info('Team config repository: %s', 'somerepo'),
            call.GitRepo.get_clone_url(),
            call.logging.info('Root config repository: %s', 'somerepo'),
            call.GitRepo.checkout('master'),
            call.GitRepo.get_full_file_path('.'),
            call.os.listdir('/tmp/created-tmp-dir/.'),
            call.os.path.isdir('/tmp/created-tmp-dir/./folder'),
            call.logging.info('Found %s app(s) in apps repository: %s', 1, 'folder'),
            call.logging.info("Searching apps repository in root repository's 'apps/' directory..."),
            call.GitRepo.checkout('master'),
            call.GitRepo.get_full_file_path('bootstrap/values.yaml'),
            call.open('/tmp/created-tmp-dir/bootstrap/values.yaml', 'r'),
            call.YAML.load(self.open_mock),
            call.logging.info('Analyzing %s in root repository', 'apps/team-non-prod.yaml'),
            call.GitRepo.get_full_file_path('apps/team-non-prod.yaml'),
            call.open('/tmp/created-tmp-dir/apps/team-non-prod.yaml', 'r'),
            call.YAML.load(self.open_mock),
            call.GitRepo.get_clone_url(),
            call.logging.info('Found apps repository in %s', 'apps/team-non-prod.yaml'),
            call.logging.info("Sync applications in root repository's %s.", 'apps/team-non-prod.yaml'),
            call.merge_yaml_element('/tmp/created-tmp-dir/apps/team-non-prod.yaml', 'applications', {'folder': {}}, True),
            call.GitRepo.get_author_from_last_commit(),
            call.GitRepo.commit('GIT_USER', 'GIT_EMAIL', "author updated apps/team-non-prod.yaml"),
            call.GitRepo.push('master'),
        ]