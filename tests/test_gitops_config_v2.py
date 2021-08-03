import unittest
import pytest

from gitopscli.gitops_config import GitOpsConfig
from gitopscli.gitops_exception import GitOpsException


class GitOpsConfigV2Test(unittest.TestCase):
    def setUp(self):
        self.yaml = {
            "apiVersion": "v2_beta",
            "applicationName": "my-app",
            "previewConfig": {
                "host": "my-${PREVIEW_ID}-${PREVIEW_ID_HASH}-host-template",
                "template": {
                    "organisation": "my-template-org",
                    "repository": "my-template-repo",
                    "branch": "my-template-branch",
                    "path": ".my-template-dir/${APPLICATION_NAME}",
                },
                "target": {
                    "organisation": "my-target-org",
                    "repository": "my-target-repo",
                    "branch": "my-target-branch",
                    "namespace": "${APPLICATION_NAME}-${PREVIEW_ID_HASH}-dev",
                },
                "replace": {
                    "file_1.yaml": [
                        {"path": "a.b", "value": "${PREVIEW_HOST}-foo"},
                        {"path": "c.d", "value": "bar-${PREVIEW_NAMESPACE}"},
                    ],
                    "file_2.yaml": [{"path": "e.f", "value": "${GIT_HASH}"}],
                },
            },
        }

    def load(self) -> GitOpsConfig:
        return GitOpsConfig.from_yaml(self.yaml)

    def assert_load_error(self, error_msg: str) -> None:
        with pytest.raises(GitOpsException) as ex:
            self.load()
        self.assertEqual(error_msg, str(ex.value))

    def test_apiVersion(self):
        config = self.load()
        self.assertEqual(config.api_version, 2)

    def test_invalid_apiVersion(self):
        self.yaml["apiVersion"] = "foo"
        self.assert_load_error("GitOps config apiVersion 'foo' is not supported!")

    def test_application_name(self):
        config = self.load()
        self.assertEqual(config.application_name, "my-app")

    def test_application_name_missing(self):
        del self.yaml["applicationName"]
        self.assert_load_error("Key 'applicationName' not found in GitOps config!")

    def test_application_name_not_a_string(self):
        self.yaml["applicationName"] = 1
        self.assert_load_error("Item 'applicationName' should be a string in GitOps config!")

    def test_preview_host_template(self):
        config = self.load()
        self.assertEqual(config.preview_host_template, "my-${PREVIEW_ID}-${PREVIEW_ID_HASH}-host-template")

    def test_preview_host(self):
        config = self.load()
        self.assertEqual(
            config.get_preview_host("PREVIEW_ID/with_odd_chars__"),
            "my-preview-id-with-odd-chars-cd2cb125-host-template",
        )

    def test_preview_host_missing(self):
        del self.yaml["previewConfig"]["host"]
        self.assert_load_error("Key 'previewConfig.host' not found in GitOps config!")

    def test_preview_host_not_a_string(self):
        self.yaml["previewConfig"]["host"] = []
        self.assert_load_error("Item 'previewConfig.host' should be a string in GitOps config!")

    def test_preview_host_contains_invalid_variable(self):
        self.yaml["previewConfig"]["host"] = "${FOO}-bar"
        self.assert_load_error("GitOps config template '${FOO}-bar' contains invalid variable: FOO")

    def test_preview_template_organisation(self):
        config = self.load()
        self.assertEqual(config.preview_template_organisation, "my-template-org")

    def test_preview_template_organisation_default(self):
        del self.yaml["previewConfig"]["template"]["organisation"]
        config = self.load()
        self.assertEqual(config.preview_template_organisation, "my-target-org")

    def test_preview_template_organisation_not_a_string(self):
        self.yaml["previewConfig"]["template"]["organisation"] = True
        self.assert_load_error("Item 'previewConfig.template.organisation' should be a string in GitOps config!")

    def test_preview_template_repository(self):
        config = self.load()
        self.assertEqual(config.preview_template_repository, "my-template-repo")

    def test_preview_template_repository_default(self):
        del self.yaml["previewConfig"]["template"]["repository"]
        config = self.load()
        self.assertEqual(config.preview_template_repository, "my-target-repo")

    def test_preview_template_repository_not_a_string(self):
        self.yaml["previewConfig"]["template"]["repository"] = []
        self.assert_load_error("Item 'previewConfig.template.repository' should be a string in GitOps config!")

    def test_preview_template_branch(self):
        config = self.load()
        self.assertEqual(config.preview_template_branch, "my-template-branch")

    def test_preview_template_branch_default(self):
        del self.yaml["previewConfig"]["template"]["branch"]
        config = self.load()
        self.assertEqual(config.preview_template_branch, "my-target-branch")

        del self.yaml["previewConfig"]["target"]["branch"]
        config = self.load()
        self.assertIsNone(config.preview_template_branch)

    def test_preview_template_branch_not_a_string(self):
        self.yaml["previewConfig"]["template"]["branch"] = []
        self.assert_load_error("Item 'previewConfig.template.branch' should be a string in GitOps config!")

    def test_preview_template_path(self):
        config = self.load()
        self.assertEqual(config.preview_template_path, ".my-template-dir/my-app")

    def test_preview_template_path_default(self):
        del self.yaml["previewConfig"]["template"]["path"]
        config = self.load()
        self.assertEqual(config.preview_template_path, ".preview-templates/my-app")

    def test_preview_template_path_not_a_string(self):
        self.yaml["previewConfig"]["template"]["path"] = []
        self.assert_load_error("Item 'previewConfig.template.path' should be a string in GitOps config!")

    def test_preview_template_path_contains_invalid_variable(self):
        self.yaml["previewConfig"]["template"]["path"] = "${FOO}-bar"
        self.assert_load_error("GitOps config template '${FOO}-bar' contains invalid variable: FOO")

    def test_preview_target_organisation(self):
        config = self.load()
        self.assertEqual(config.preview_target_organisation, "my-target-org")

    def test_preview_target_organisation_missing(self):
        del self.yaml["previewConfig"]["target"]["organisation"]
        self.assert_load_error("Key 'previewConfig.target.organisation' not found in GitOps config!")

    def test_preview_target_organisation_not_a_string(self):
        self.yaml["previewConfig"]["target"]["organisation"] = []
        self.assert_load_error("Item 'previewConfig.target.organisation' should be a string in GitOps config!")

    def test_preview_target_repository(self):
        config = self.load()
        self.assertEqual(config.preview_target_repository, "my-target-repo")

    def test_preview_target_repository_missing(self):
        del self.yaml["previewConfig"]["target"]["repository"]
        self.assert_load_error("Key 'previewConfig.target.repository' not found in GitOps config!")

    def test_preview_target_repository_not_a_string(self):
        self.yaml["previewConfig"]["target"]["repository"] = []
        self.assert_load_error("Item 'previewConfig.target.repository' should be a string in GitOps config!")

    def test_preview_target_branch(self):
        config = self.load()
        self.assertEqual(config.preview_target_branch, "my-target-branch")

    def test_preview_target_branch_default(self):
        del self.yaml["previewConfig"]["target"]["branch"]
        config = self.load()
        self.assertIsNone(config.preview_target_branch)

    def test_preview_target_branch_not_a_string(self):
        self.yaml["previewConfig"]["target"]["branch"] = []
        self.assert_load_error("Item 'previewConfig.target.branch' should be a string in GitOps config!")

    def test_is_preview_template_equal_target(self):
        for x in {"organisation", "repository", "branch"}:
            self.yaml["previewConfig"]["template"][x] = self.yaml["previewConfig"]["target"][x]

        for x in {"organisation", "repository", "branch"}:
            self.yaml["previewConfig"]["template"][x] = "custom-template-value"
            config = self.load()
            self.assertFalse(config.is_preview_template_equal_target(), x)

            del self.yaml["previewConfig"]["template"][x]
            config = self.load()
            self.assertTrue(config.is_preview_template_equal_target(), x)

            self.yaml["previewConfig"]["template"][x] = self.yaml["previewConfig"]["target"][x]
            config = self.load()
            self.assertTrue(config.is_preview_template_equal_target(), x)

    def test_preview_target_namespace(self):
        config = self.load()
        self.assertEqual(config.preview_target_namespace_template, "${APPLICATION_NAME}-${PREVIEW_ID_HASH}-dev")
        self.assertEqual(config.get_preview_namespace("preview-1"), "my-app-3e355b4a-dev")

    def test_preview_target_namespace_default(self):
        del self.yaml["previewConfig"]["target"]["namespace"]
        config = self.load()
        self.assertEqual(
            config.preview_target_namespace_template, "${APPLICATION_NAME}-${PREVIEW_ID}-${PREVIEW_ID_HASH}-preview"
        )
        actual_namespace = config.get_preview_namespace(
            "Very long preview ID. It will be cut to have max 63 chars of namespace in total!!"
        )
        self.assertEqual(actual_namespace, "my-app-very-long-preview-id-it-will-be-cut-to-05d9825a-preview")
        self.assertTrue(len(actual_namespace) <= 63)

    def test_preview_target_namespace_not_a_string(self):
        self.yaml["previewConfig"]["target"]["namespace"] = []
        self.assert_load_error("Item 'previewConfig.target.namespace' should be a string in GitOps config!")

    def test_preview_target_namespace_invalid_template(self):
        self.yaml["previewConfig"]["target"]["namespace"] = "-*+§-weird chars-${PREVIEW_ID_HASH}"
        config = self.load()
        with pytest.raises(GitOpsException) as ex:
            config.get_preview_namespace("preview-1")
        self.assertEqual("Invalid character in preview namespace: '*'", str(ex.value))

    def test_preview_target_namespace_too_long(self):
        self.yaml["previewConfig"]["target"][
            "namespace"
        ] = "veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery-long-${PREVIEW_ID}-${PREVIEW_ID_HASH}"
        config = self.load()
        with pytest.raises(GitOpsException) as ex:
            config.get_preview_namespace("x")
        self.assertEqual(
            "Preview namespace is too long (max 63 chars): veeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeery-long--2d711642 (68 chars)",
            str(ex.value),
        )

    def test_preview_target_namespace_contains_invalid_variable(self):
        self.yaml["previewConfig"]["target"]["namespace"] = "${FOO}-bar"
        self.assert_load_error("GitOps config template '${FOO}-bar' contains invalid variable: FOO")

    def test_replacements(self):
        config = self.load()
        self.assertEqual(config.replacements.keys(), {"file_1.yaml", "file_2.yaml"})

        self.assertEqual(len(config.replacements["file_1.yaml"]), 2)
        self.assertEqual(config.replacements["file_1.yaml"][0].path, "a.b")
        self.assertEqual(config.replacements["file_1.yaml"][0].value_template, "${PREVIEW_HOST}-foo")
        self.assertEqual(config.replacements["file_1.yaml"][1].path, "c.d")
        self.assertEqual(config.replacements["file_1.yaml"][1].value_template, "bar-${PREVIEW_NAMESPACE}")

        self.assertEqual(len(config.replacements["file_2.yaml"]), 1)
        self.assertEqual(config.replacements["file_2.yaml"][0].path, "e.f")
        self.assertEqual(config.replacements["file_2.yaml"][0].value_template, "${GIT_HASH}")

    def test_replacements_missing(self):
        del self.yaml["previewConfig"]["replace"]
        self.assert_load_error("Key 'previewConfig.replace' not found in GitOps config!")

    def test_replacements_not_an_object(self):
        self.yaml["previewConfig"]["replace"] = "foo"
        self.assert_load_error("Item 'previewConfig.replace' should be an object in GitOps config!")

    def test_replacements_file_item_not_a_list(self):
        self.yaml["previewConfig"]["replace"]["file_1.yaml"] = 1
        self.assert_load_error("Item 'previewConfig.replace.file_1\\.yaml' should be a list in GitOps config!")

    def test_replacements_invalid_list(self):
        self.yaml["previewConfig"]["replace"]["file_1.yaml"] = ["foo"]
        self.assert_load_error("Item 'previewConfig.replace.file_1\\.yaml.[0]' should be an object in GitOps config!")

    def test_replacements_invalid_list_items_missing_path(self):
        del self.yaml["previewConfig"]["replace"]["file_1.yaml"][1]["path"]
        self.assert_load_error("Key 'previewConfig.replace.file_1\\.yaml.[1].path' not found in GitOps config!")

    def test_replacements_invalid_list_items_missing_value(self):
        del self.yaml["previewConfig"]["replace"]["file_1.yaml"][0]["value"]
        self.assert_load_error("Key 'previewConfig.replace.file_1\\.yaml.[0].value' not found in GitOps config!")

    def test_replacements_invalid_list_items_path_not_a_string(self):
        self.yaml["previewConfig"]["replace"]["file_1.yaml"][0]["path"] = 42
        self.assert_load_error(
            "Item 'previewConfig.replace.file_1\\.yaml.[0].path' should be a string in GitOps config!"
        )

    def test_replacements_invalid_list_items_value_not_a_string(self):
        self.yaml["previewConfig"]["replace"]["file_2.yaml"][0]["value"] = []
        self.assert_load_error(
            "Item 'previewConfig.replace.file_2\\.yaml.[0].value' should be a string in GitOps config!"
        )

    def test_replacements_invalid_list_items_unknown_variable(self):
        self.yaml["previewConfig"]["replace"]["file_2.yaml"][0]["value"] = "${FOO}bar"
        self.assert_load_error("Replacement value '${FOO}bar' for path 'e.f' contains invalid variable: FOO")
