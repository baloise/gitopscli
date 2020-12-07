import unittest
import pytest

from gitopscli.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException


class GitOpsConfigTest(unittest.TestCase):
    def setUp(self):
        self.yaml = {
            "deploymentConfig": {"applicationName": "my-app", "org": "my-org", "repository": "my-repo"},
            "previewConfig": {
                "route": {"host": {"template": "my-host-template"}},
                "replace": [{"path": "a.b", "variable": "ROUTE_HOST"}, {"path": "c.d", "variable": "GIT_COMMIT"}],
            },
        }

    def load(self) -> GitOpsConfig:
        return GitOpsConfig.from_yaml(self.yaml)

    def assert_load_error(self, error_msg: str) -> None:
        with pytest.raises(GitOpsException) as ex:
            self.load()
        self.assertEqual(error_msg, str(ex.value))

    def test_application_name(self):
        config = self.load()
        self.assertEqual(config.application_name, "my-app")

    def test_application_name_missing(self):
        del self.yaml["deploymentConfig"]["applicationName"]
        self.assert_load_error("Key 'deploymentConfig.applicationName' not found in GitOps config!")

    def test_application_name_not_a_string(self):
        self.yaml["deploymentConfig"]["applicationName"] = 1
        self.assert_load_error("Item 'deploymentConfig.applicationName' should be a string in GitOps config!")

    def test_team_config_org(self):
        config = self.load()
        self.assertEqual(config.team_config_org, "my-org")

    def test_team_config_org_missing(self):
        del self.yaml["deploymentConfig"]["org"]
        self.assert_load_error("Key 'deploymentConfig.org' not found in GitOps config!")

    def test_team_config_org_not_a_string(self):
        self.yaml["deploymentConfig"]["org"] = True
        self.assert_load_error("Item 'deploymentConfig.org' should be a string in GitOps config!")

    def test_team_config_repo(self):
        config = self.load()
        self.assertEqual(config.team_config_repo, "my-repo")

    def test_team_config_repo_missing(self):
        del self.yaml["deploymentConfig"]["repository"]
        self.assert_load_error("Key 'deploymentConfig.repository' not found in GitOps config!")

    def test_team_config_repo_not_a_string(self):
        self.yaml["deploymentConfig"]["repository"] = []
        self.assert_load_error("Item 'deploymentConfig.repository' should be a string in GitOps config!")

    def test_route_host_template(self):
        config = self.load()
        self.assertEqual(config.route_host_template, "my-host-template")

    def test_route_missing(self):
        del self.yaml["previewConfig"]["route"]
        self.assert_load_error("Key 'previewConfig.route.host.template' not found in GitOps config!")

    def test_route_host_missing(self):
        del self.yaml["previewConfig"]["route"]["host"]
        self.assert_load_error("Key 'previewConfig.route.host.template' not found in GitOps config!")

    def test_route_host_template_missing(self):
        del self.yaml["previewConfig"]["route"]["host"]["template"]
        self.assert_load_error("Key 'previewConfig.route.host.template' not found in GitOps config!")

    def test_route_host_template_not_a_string(self):
        self.yaml["previewConfig"]["route"]["host"]["template"] = []
        self.assert_load_error("Item 'previewConfig.route.host.template' should be a string in GitOps config!")

    def test_replacements(self):
        config = self.load()
        self.assertEqual(
            config.replacements,
            [
                GitOpsConfig.Replacement(path="a.b", variable=GitOpsConfig.Replacement.Variable.ROUTE_HOST),
                GitOpsConfig.Replacement(path="c.d", variable=GitOpsConfig.Replacement.Variable.GIT_COMMIT),
            ],
        )

    def test_replacements_missing(self):
        del self.yaml["previewConfig"]["replace"]
        self.assert_load_error("Key 'previewConfig.replace' not found in GitOps config!")

    def test_replacements_not_a_list(self):
        self.yaml["previewConfig"]["replace"] = "foo"
        self.assert_load_error("Item 'previewConfig.replace' should be a list in GitOps config!")

    def test_replacements_invalid_list(self):
        self.yaml["previewConfig"]["replace"] = ["foo"]
        self.assert_load_error("Item 'previewConfig.replace.[0]' should be a object in GitOps config!")

    def test_replacements_invalid_list_items_missing_path(self):
        del self.yaml["previewConfig"]["replace"][1]["path"]
        self.assert_load_error("Key 'previewConfig.replace.[1].path' not found in GitOps config!")

    def test_replacements_invalid_list_items_missing_variable(self):
        del self.yaml["previewConfig"]["replace"][0]["variable"]
        self.assert_load_error("Key 'previewConfig.replace.[0].variable' not found in GitOps config!")

    def test_replacements_invalid_list_items_path_not_a_string(self):
        self.yaml["previewConfig"]["replace"][0]["path"] = 42
        self.assert_load_error("Item 'previewConfig.replace.[0].path' should be a string in GitOps config!")

    def test_replacements_invalid_list_items_variable_not_a_string(self):
        self.yaml["previewConfig"]["replace"][0]["variable"] = []
        self.assert_load_error("Item 'previewConfig.replace.[0].variable' should be a string in GitOps config!")

    def test_replacements_invalid_list_items_unknown_variable(self):
        self.yaml["previewConfig"]["replace"][0]["variable"] = "FOO"
        self.assert_load_error(
            "Item 'previewConfig.replace.[0].variable' should be one of the following values in GitOps config: GIT_COMMIT, ROUTE_HOST"
        )
