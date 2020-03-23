import os
import shutil
import unittest
import uuid
import pytest

from gitopscli.yaml.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException


class GitOpsConfigTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = f"/tmp/gitopscli-test-{uuid.uuid4()}"
        os.makedirs(cls.tmp_dir)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    def _create_file(self, content):
        path = f"{self.tmp_dir}/{uuid.uuid4()}"
        with open(path, "w+") as stream:
            stream.write(content)
        return path

    def test_application_name(self):
        test_file = self._create_file("deploymentConfig: { applicationName: my-app }")
        config = GitOpsConfig(test_file)
        self.assertEqual(config.application_name, "my-app")

    def test_application_name_missing(self):
        test_file = self._create_file("deploymentConfig: { }")

        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.application_name  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'deploymentConfig.applicationName' not found in GitOps config!")

    def test_application_name_not_a_string(self):
        test_file = self._create_file("deploymentConfig: { applicationName: [] }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.application_name  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'deploymentConfig.applicationName' should be a string in GitOps config!")

    def test_team_config_org(self):
        test_file = self._create_file("deploymentConfig: { org: my-org }")
        config = GitOpsConfig(test_file)
        self.assertEqual(config.team_config_org, "my-org")

    def test_team_config_org_missing(self):
        test_file = self._create_file("deploymentConfig: { }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.team_config_org  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'deploymentConfig.org' not found in GitOps config!")

    def test_team_config_org_not_a_string(self):
        test_file = self._create_file("deploymentConfig: { org: [] }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.team_config_org  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'deploymentConfig.org' should be a string in GitOps config!")

    def test_team_config_repo(self):
        test_file = self._create_file("deploymentConfig: { repository: my-repo }")
        config = GitOpsConfig(test_file)
        self.assertEqual(config.team_config_repo, "my-repo")

    def test_team_config_repo_missing(self):
        test_file = self._create_file("deploymentConfig: { }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.team_config_repo  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'deploymentConfig.repository' not found in GitOps config!")

    def test_team_config_repo_not_a_string(self):
        test_file = self._create_file("deploymentConfig: { repository: [] }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.team_config_repo  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'deploymentConfig.repository' should be a string in GitOps config!")

    def test_route_host(self):
        test_file = self._create_file("previewConfig: { route: { host: { template: my-host-template } } }")
        config = GitOpsConfig(test_file)
        self.assertEqual(config.route_host, "my-host-template")

    def test_route_host_missing(self):
        test_file = self._create_file("previewConfig: { route: { } }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.route_host  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'previewConfig.route.host.template' not found in GitOps config!")

        test_file = self._create_file("previewConfig: { route: { host: {  } } }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.route_host  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'previewConfig.route.host.template' not found in GitOps config!")

    def test_route_host_not_a_string(self):
        test_file = self._create_file("previewConfig: { route: { host: { template: 1 } } }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.route_host  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'previewConfig.route.host.template' should be a string in GitOps config!")

    def test_replacements(self):
        test_file = self._create_file("previewConfig: { replace: [ { path: p, variable: v } ] }")
        config = GitOpsConfig(test_file)
        self.assertEqual(config.replacements, [{"path": "p", "variable": "v"}])

    def test_replacements_missing(self):
        test_file = self._create_file("previewConfig: { }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.replacements  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'previewConfig.replace' not found in GitOps config!")

    def test_replacements_not_a_list(self):
        test_file = self._create_file("previewConfig: { replace: 1 }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.replacements  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Key 'previewConfig.replace' should be a list in GitOps config!")

    def test_replacements_invalid_list_items(self):
        test_file = self._create_file("previewConfig: { replace: [ invalid ] }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.replacements  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Every item in 'previewConfig.replace' should have a 'path' and and 'variabe'!")

        test_file = self._create_file("previewConfig: { replace: [ { variable: v } ] }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.replacements  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Every item in 'previewConfig.replace' should have a 'path' and and 'variabe'!")

        test_file = self._create_file("previewConfig: { replace: [ { path: p } ] }")
        config = GitOpsConfig(test_file)
        with pytest.raises(GitOpsException) as ex:
            config.replacements  # pylint: disable=pointless-statement
        self.assertEqual(str(ex.value), "Every item in 'previewConfig.replace' should have a 'path' and and 'variabe'!")
