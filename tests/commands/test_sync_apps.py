import posixpath
import logging
import os
import unittest
from unittest.mock import call
from gitopscli.git_api import GitProvider, GitRepo, GitRepoApi, GitRepoApiFactory
from gitopscli.commands.sync_apps import SyncAppsCommand
from gitopscli.io_api.yaml_util import merge_yaml_element, yaml_file_load
from gitopscli.gitops_exception import GitOpsException

# from collections import OrderedDict as ordereddict
from ruamel.yaml.compat import ordereddict
from .mock_mixin import MockMixin

ARGS = SyncAppsCommand.Args(
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


class SyncAppsCommandTest(MockMixin, unittest.TestCase):
    def setUp(self):
        self.init_mock_manager(SyncAppsCommand)

        self.os_mock = self.monkey_patch(os)
        self.os_mock.path.isdir.return_value = True
        self.os_mock.path.join.side_effect = posixpath.join  # tests are designed to emulate posix env
        self.os_mock.listdir.return_value = ["my-app"]
        self.os_mock.path.exists.return_value = False

        self.logging_mock = self.monkey_patch(logging)
        self.logging_mock.info.return_value = None

        self.team_config_git_repo_api_mock = self.create_mock(GitRepoApi)
        self.root_config_git_repo_api_mock = self.create_mock(GitRepoApi)

        self.team_config_git_repo_mock = self.create_mock(GitRepo, "GitRepo_team")
        self.team_config_git_repo_mock.__enter__.return_value = self.team_config_git_repo_mock
        self.team_config_git_repo_mock.__exit__.return_value = False
        self.team_config_git_repo_mock.get_clone_url.return_value = "https://repository.url/team/team-non-prod.git"
        self.team_config_git_repo_mock.clone.return_value = None
        self.team_config_git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/team-config-repo/{x}"
        self.team_config_git_repo_mock.get_author_from_last_commit.return_value = "author"

        self.root_config_git_repo_mock = self.create_mock(GitRepo, "GitRepo_root")
        self.root_config_git_repo_mock.__enter__.return_value = self.root_config_git_repo_mock
        self.root_config_git_repo_mock.__exit__.return_value = False
        self.root_config_git_repo_mock.get_full_file_path.side_effect = lambda x: f"/tmp/root-config-repo/{x}"
        self.root_config_git_repo_mock.get_clone_url.return_value = "https://repository.url/root/root-config.git"
        self.root_config_git_repo_mock.clone.return_value = None
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
        self.yaml_file_load_mock.side_effect = lambda file_path: {
            "/tmp/root-config-repo/bootstrap/values.yaml": {
                "bootstrap": [{"name": "team-non-prod"}, {"name": "other-team-non-prod"}],
            },
            "/tmp/root-config-repo/apps/team-non-prod.yaml": {
                "config": {
                    "repository": "https://repository.url/team/team-non-prod.git",
                    "applications": {"some-other-app-1": None},
                }
            },
            "/tmp/root-config-repo/apps/other-team-non-prod.yaml": {
                "repository": "https://repository.url/other-team/other-team-non-prod.git",
                "applications": {"some-other-app-2": None},
            },
        }[file_path]

        self.merge_yaml_element_mock = self.monkey_patch(merge_yaml_element)
        self.merge_yaml_element_mock.return_value = None

        self.seal_mocks()

    def test_sync_apps_happy_flow(self):
        SyncAppsCommand(ARGS).execute()
        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(ARGS, "TEAM_ORGA", "TEAM_REPO"),
            call.GitRepoApiFactory.create(ARGS, "ROOT_ORGA", "ROOT_REPO"),
            call.GitRepo(self.team_config_git_repo_api_mock),
            call.GitRepo(self.root_config_git_repo_api_mock),
            call.GitRepo_team.get_clone_url(),
            call.logging.info("Team config repository: %s", "https://repository.url/team/team-non-prod.git"),
            call.GitRepo_root.get_clone_url(),
            call.logging.info("Root config repository: %s", "https://repository.url/root/root-config.git"),
            call.GitRepo_root.get_clone_url(),
            call.GitRepo_root.clone(),
            call.GitRepo_root.get_full_file_path("bootstrap/values.yaml"),
            call.yaml_file_load("/tmp/root-config-repo/bootstrap/values.yaml"),
            call.logging.info("Analyzing %s in root repository", "apps/team-non-prod.yaml"),
            call.GitRepo_root.get_full_file_path("apps/team-non-prod.yaml"),
            call.yaml_file_load("/tmp/root-config-repo/apps/team-non-prod.yaml"),
            call.logging.info("adding %s", "team-non-prod"),
            call.logging.info("Analyzing %s in root repository", "apps/other-team-non-prod.yaml"),
            call.GitRepo_root.get_full_file_path("apps/other-team-non-prod.yaml"),
            call.yaml_file_load("/tmp/root-config-repo/apps/other-team-non-prod.yaml"),
            call.logging.info("adding %s", "other-team-non-prod"),
            call.GitRepo_team.get_clone_url(),
            call.GitRepo_team.clone(),
            call.GitRepo_team.get_full_file_path("."),
            call.os.listdir("/tmp/team-config-repo/."),
            call.os.path.join("/tmp/team-config-repo/.", "my-app"),
            call.os.path.isdir("/tmp/team-config-repo/./my-app"),
            call.GitRepo_team.get_clone_url(),
            call.GitRepo_team.get_full_file_path("my-app/app_value_file.yaml"),
            call.os.path.exists("/tmp/team-config-repo/my-app/app_value_file.yaml"),
            call.GitRepo_team.get_clone_url(),
            call.logging.info("Found %s app(s) in apps repository: %s", 1, "my-app"),
            call.logging.info("Searching apps repository in root repository's 'apps/' directory..."),
            call.logging.info("Sync applications in root repository's %s.", "apps/team-non-prod.yaml"),
            call.merge_yaml_element(
                "/tmp/root-config-repo/apps/team-non-prod.yaml",
                "config.applications",
                {"my-app": ordereddict([("customAppConfig", None)])},
            ),
            call.GitRepo_team.get_author_from_last_commit(),
            call.GitRepo_root.commit("GIT_USER", "GIT_EMAIL", "author updated apps/team-non-prod.yaml"),
            call.GitRepo_root.push(),
        ]

    def test_sync_apps_already_up_to_date(self):
        self.yaml_file_load_mock.side_effect = lambda file_path: {
            "/tmp/root-config-repo/bootstrap/values.yaml": {
                "bootstrap": [{"name": "team-non-prod"}, {"name": "other-team-non-prod"}],
            },
            "/tmp/root-config-repo/apps/team-non-prod.yaml": {
                "repository": "https://repository.url/team/team-non-prod.git",
                "applications": {"my-app": ordereddict([("customAppConfig", None)])},  # my-app already exists
            },
            "/tmp/root-config-repo/apps/other-team-non-prod.yaml": {
                "repository": "https://repository.url/other-team/other-team-non-prod.git",
                "applications": {},
            },
        }[file_path]

        SyncAppsCommand(ARGS).execute()
        assert self.mock_manager.method_calls == [
            call.GitRepoApiFactory.create(ARGS, "TEAM_ORGA", "TEAM_REPO"),
            call.GitRepoApiFactory.create(ARGS, "ROOT_ORGA", "ROOT_REPO"),
            call.GitRepo(self.team_config_git_repo_api_mock),
            call.GitRepo(self.root_config_git_repo_api_mock),
            call.GitRepo_team.get_clone_url(),
            call.logging.info("Team config repository: %s", "https://repository.url/team/team-non-prod.git"),
            call.GitRepo_root.get_clone_url(),
            call.logging.info("Root config repository: %s", "https://repository.url/root/root-config.git"),
            call.GitRepo_root.get_clone_url(),
            call.GitRepo_root.clone(),
            call.GitRepo_root.get_full_file_path("bootstrap/values.yaml"),
            call.yaml_file_load("/tmp/root-config-repo/bootstrap/values.yaml"),
            call.logging.info("Analyzing %s in root repository", "apps/team-non-prod.yaml"),
            call.GitRepo_root.get_full_file_path("apps/team-non-prod.yaml"),
            call.yaml_file_load("/tmp/root-config-repo/apps/team-non-prod.yaml"),
            call.logging.info("adding %s", "team-non-prod"),
            call.logging.info("Analyzing %s in root repository", "apps/other-team-non-prod.yaml"),
            call.GitRepo_root.get_full_file_path("apps/other-team-non-prod.yaml"),
            call.yaml_file_load("/tmp/root-config-repo/apps/other-team-non-prod.yaml"),
            call.logging.info("adding %s", "other-team-non-prod"),
            call.GitRepo_team.get_clone_url(),
            call.GitRepo_team.clone(),
            call.GitRepo_team.get_full_file_path("."),
            call.os.listdir("/tmp/team-config-repo/."),
            call.os.path.join("/tmp/team-config-repo/.", "my-app"),
            call.os.path.isdir("/tmp/team-config-repo/./my-app"),
            call.GitRepo_team.get_clone_url(),
            call.GitRepo_team.get_full_file_path("my-app/app_value_file.yaml"),
            call.os.path.exists("/tmp/team-config-repo/my-app/app_value_file.yaml"),
            call.GitRepo_team.get_clone_url(),
            call.logging.info("Found %s app(s) in apps repository: %s", 1, "my-app"),
            call.logging.info("Searching apps repository in root repository's 'apps/' directory..."),
            call.logging.info("Root repository already up-to-date. I'm done here."),
        ]

    def test_sync_apps_bootstrap_yaml_not_found(self):
        self.yaml_file_load_mock.side_effect = FileNotFoundError()

        try:
            SyncAppsCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("File 'bootstrap/values.yaml' not found in root repository.", str(ex))

    def test_sync_apps_missing_bootstrap_element_in_bootstrap_yaml(self):
        self.yaml_file_load_mock.side_effect = lambda file_path: {
            "/tmp/root-config-repo/bootstrap/values.yaml": {},  # empty bootstrap yaml
        }[file_path]

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
        try:
            SyncAppsCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("Cannot find key 'bootstrap' in 'bootstrap/values.yaml'", str(ex))

    def test_sync_apps_invalid_bootstrap_entry_in_bootstrap_yaml(self):
        self.yaml_file_load_mock.side_effect = lambda file_path: {
            "/tmp/root-config-repo/bootstrap/values.yaml": {
                "bootstrap": [{"something": "invalid"}],  # bootstrap entry has no "name" property
            },
        }[file_path]

        try:
            SyncAppsCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("Every bootstrap entry must have a 'name' property.", str(ex))

    def test_sync_apps_team_yaml_not_found(self):
        def file_load_mock_side_effect(file_path):
            if file_path == "/tmp/root-config-repo/bootstrap/values.yaml":
                return {
                    "bootstrap": [{"name": "team-non-prod"}],
                }
            if file_path == "/tmp/root-config-repo/apps/team-non-prod.yaml":
                raise FileNotFoundError()
            raise Exception("test should not reach this")

        self.yaml_file_load_mock.side_effect = file_load_mock_side_effect

        try:
            SyncAppsCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("File 'apps/team-non-prod.yaml' not found in root repository.", str(ex))

    def test_sync_apps_missing_repository_element_in_team_yaml(self):
        self.yaml_file_load_mock.side_effect = lambda file_path: {
            "/tmp/root-config-repo/bootstrap/values.yaml": {"bootstrap": [{"name": "team-non-prod"}]},
            "/tmp/root-config-repo/apps/team-non-prod.yaml": {
                # missing: "repository": "https://repository.url/team/team-non-prod.git",
                "applications": {},
            },
        }[file_path]

        try:
            SyncAppsCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("Cannot find key 'repository' in 'apps/team-non-prod.yaml'", str(ex))

    def test_sync_apps_undefined_team_repo(self):
        self.yaml_file_load_mock.side_effect = lambda file_path: {
            "/tmp/root-config-repo/bootstrap/values.yaml": {"bootstrap": [{"name": "other-team-non-prod"}]},
            "/tmp/root-config-repo/apps/other-team-non-prod.yaml": {
                "repository": "https://repository.url/other-team/other-team-non-prod.git",  # there is no repo matching the command's team repo
                "applications": {},
            },
        }[file_path]

        try:
            SyncAppsCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual(
                "Couldn't find config file for apps repository in root repository's 'apps/' directory", str(ex)
            )

    def test_sync_apps_app_name_collission(self):
        self.yaml_file_load_mock.side_effect = lambda file_path: {
            "/tmp/root-config-repo/bootstrap/values.yaml": {
                "bootstrap": [{"name": "team-non-prod"}, {"name": "other-team-non-prod"}],
            },
            "/tmp/root-config-repo/apps/team-non-prod.yaml": {
                "repository": "https://repository.url/team/team-non-prod.git",
                "applications": {"some-other-app-1": None},
            },
            "/tmp/root-config-repo/apps/other-team-non-prod.yaml": {
                "repository": "https://repository.url/other-team/other-team-non-prod.git",
                "applications": {"my-app": None},  # the other-team already has an app named "my-app"
            },
        }[file_path]

        try:
            SyncAppsCommand(ARGS).execute()
            self.fail()
        except GitOpsException as ex:
            self.assertEqual("Application 'my-app' already exists in a different repository", str(ex))
