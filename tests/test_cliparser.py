import sys
import unittest
from contextlib import contextmanager
from io import StringIO
import pytest

from gitopscli.cliparser import create_cli

EXPECTED_GITOPSCLI_HELP = """\
usage: gitopscli [-h]
                 {deploy,sync-apps,add-pr-comment,create-preview,delete-preview}
                 ...

GitOps CLI

optional arguments:
  -h, --help            show this help message and exit

commands:
  {deploy,sync-apps,add-pr-comment,create-preview,delete-preview}
    deploy              Trigger a new deployment by changing YAML values
    sync-apps           Synchronize applications (= every directory) from apps
                        config repository to apps root config
    add-pr-comment      Create a comment on the pull request
    create-preview      Create a preview environment
    delete-preview      Delete a preview environment
"""

EXPECTED_ADD_PR_COMMENT_NO_ARGS_ERROR = """\
usage: gitopscli add-pr-comment [-h] --username USERNAME --password PASSWORD
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL] --pr-id
                                PR_ID [--parent-id PARENT_ID] [-v [VERBOSE]]
                                --text TEXT
gitopscli add-pr-comment: error: the following arguments are required: --username, --password, --organisation, --repository-name, --pr-id, --text
"""

EXPECTED_ADD_PR_COMMENT_HELP = """\
usage: gitopscli add-pr-comment [-h] --username USERNAME --password PASSWORD
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL] --pr-id
                                PR_ID [--parent-id PARENT_ID] [-v [VERBOSE]]
                                --text TEXT

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   Git username
  --password PASSWORD   Git password or token
  --organisation ORGANISATION
                        Apps Git organisation/projectKey
  --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  --git-provider GIT_PROVIDER
                        Git server provider
  --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
  --pr-id PR_ID         the id of the pull request
  --parent-id PARENT_ID
                        the id of the parent comment, in case of a reply
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
  --text TEXT           the text of the comment
"""

EXPECTED_CREATE_PREVIEW_NO_ARGS_ERROR = """\
usage: gitopscli create-preview [-h] --username USERNAME --password PASSWORD
                                [--git-user GIT_USER] [--git-email GIT_EMAIL]
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL]
                                [--create-pr [CREATE_PR]]
                                [--auto-merge [AUTO_MERGE]] --pr-id PR_ID
                                [--parent-id PARENT_ID] [-v [VERBOSE]]
gitopscli create-preview: error: the following arguments are required: --username, --password, --organisation, --repository-name, --pr-id
"""

EXPECTED_CREATE_PREVIEW_HELP = """\
usage: gitopscli create-preview [-h] --username USERNAME --password PASSWORD
                                [--git-user GIT_USER] [--git-email GIT_EMAIL]
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL]
                                [--create-pr [CREATE_PR]]
                                [--auto-merge [AUTO_MERGE]] --pr-id PR_ID
                                [--parent-id PARENT_ID] [-v [VERBOSE]]

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   Git username
  --password PASSWORD   Git password or token
  --git-user GIT_USER   Git Username
  --git-email GIT_EMAIL
                        Git User Email
  --organisation ORGANISATION
                        Apps Git organisation/projectKey
  --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  --git-provider GIT_PROVIDER
                        Git server provider
  --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
  --create-pr [CREATE_PR]
                        Creates a Pull Request
  --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with
                        --create-pr)
  --pr-id PR_ID         the id of the pull request
  --parent-id PARENT_ID
                        the id of the parent comment, in case of a reply
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
"""

EXPECTED_DELETE_PREVIEW_NO_ARGS_ERROR = """\
usage: gitopscli delete-preview [-h] --username USERNAME --password PASSWORD
                                [--git-user GIT_USER] [--git-email GIT_EMAIL]
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL] --branch
                                BRANCH [--create-pr [CREATE_PR]]
                                [--auto-merge [AUTO_MERGE]] [-v [VERBOSE]]
gitopscli delete-preview: error: the following arguments are required: --username, --password, --organisation, --repository-name, --branch
"""

EXPECTED_DELETE_PREVIEW_HELP = """\
usage: gitopscli delete-preview [-h] --username USERNAME --password PASSWORD
                                [--git-user GIT_USER] [--git-email GIT_EMAIL]
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL] --branch
                                BRANCH [--create-pr [CREATE_PR]]
                                [--auto-merge [AUTO_MERGE]] [-v [VERBOSE]]

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   Git username
  --password PASSWORD   Git password or token
  --git-user GIT_USER   Git Username
  --git-email GIT_EMAIL
                        Git User Email
  --organisation ORGANISATION
                        Apps Git organisation/projectKey
  --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  --git-provider GIT_PROVIDER
                        Git server provider
  --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
  --branch BRANCH       The branch for which the preview was created for
  --create-pr [CREATE_PR]
                        Creates a Pull Request
  --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with
                        --create-pr)
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
"""

EXPECTED_DEPLOY_NO_ARGS_ERROR = """\
usage: gitopscli deploy [-h] --file FILE --values VALUES
                        [--single-commit [SINGLE_COMMIT]] --username USERNAME
                        --password PASSWORD [--git-user GIT_USER]
                        [--git-email GIT_EMAIL] --organisation ORGANISATION
                        --repository-name REPOSITORY_NAME
                        [--git-provider GIT_PROVIDER]
                        [--git-provider-url GIT_PROVIDER_URL]
                        [--create-pr [CREATE_PR]] [--auto-merge [AUTO_MERGE]]
                        [-v [VERBOSE]]
gitopscli deploy: error: the following arguments are required: --file, --values, --username, --password, --organisation, --repository-name
"""

EXPECTED_DEPLOY_HELP = """\
usage: gitopscli deploy [-h] --file FILE --values VALUES
                        [--single-commit [SINGLE_COMMIT]] --username USERNAME
                        --password PASSWORD [--git-user GIT_USER]
                        [--git-email GIT_EMAIL] --organisation ORGANISATION
                        --repository-name REPOSITORY_NAME
                        [--git-provider GIT_PROVIDER]
                        [--git-provider-url GIT_PROVIDER_URL]
                        [--create-pr [CREATE_PR]] [--auto-merge [AUTO_MERGE]]
                        [-v [VERBOSE]]

optional arguments:
  -h, --help            show this help message and exit
  --file FILE           YAML file path
  --values VALUES       YAML/JSON object with the YAML path as key and the
                        desired value as value
  --single-commit [SINGLE_COMMIT]
                        Create only single commit for all updates
  --username USERNAME   Git username
  --password PASSWORD   Git password or token
  --git-user GIT_USER   Git Username
  --git-email GIT_EMAIL
                        Git User Email
  --organisation ORGANISATION
                        Apps Git organisation/projectKey
  --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  --git-provider GIT_PROVIDER
                        Git server provider
  --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
  --create-pr [CREATE_PR]
                        Creates a Pull Request
  --auto-merge [AUTO_MERGE]
                        Automatically merge the created PR (only valid with
                        --create-pr)
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
"""

EXPECTED_SYNC_APPS_NO_ARGS_ERROR = """\
usage: gitopscli sync-apps [-h] --username USERNAME --password PASSWORD
                           [--git-user GIT_USER] [--git-email GIT_EMAIL]
                           --organisation ORGANISATION --repository-name
                           REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                           [--git-provider-url GIT_PROVIDER_URL]
                           [-v [VERBOSE]] --root-organisation
                           ROOT_ORGANISATION --root-repository-name
                           ROOT_REPOSITORY_NAME
gitopscli sync-apps: error: the following arguments are required: --username, --password, --organisation, --repository-name, --root-organisation, --root-repository-name
"""

EXPECTED_SYNC_APPS_HELP = """\
usage: gitopscli sync-apps [-h] --username USERNAME --password PASSWORD
                           [--git-user GIT_USER] [--git-email GIT_EMAIL]
                           --organisation ORGANISATION --repository-name
                           REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                           [--git-provider-url GIT_PROVIDER_URL]
                           [-v [VERBOSE]] --root-organisation
                           ROOT_ORGANISATION --root-repository-name
                           ROOT_REPOSITORY_NAME

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   Git username
  --password PASSWORD   Git password or token
  --git-user GIT_USER   Git Username
  --git-email GIT_EMAIL
                        Git User Email
  --organisation ORGANISATION
                        Apps Git organisation/projectKey
  --repository-name REPOSITORY_NAME
                        Git repository name (not the URL, e.g. my-repo)
  --git-provider GIT_PROVIDER
                        Git server provider
  --git-provider-url GIT_PROVIDER_URL
                        Git provider base API URL (e.g.
                        https://bitbucket.example.tld)
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
  --root-organisation ROOT_ORGANISATION
                        Root config repository organisation
  --root-repository-name ROOT_REPOSITORY_NAME
                        Root config repository name
"""


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class CliParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    @staticmethod
    def _capture_create_cli(args):
        with captured_output() as (stdout, stderr), pytest.raises(SystemExit) as ex:
            create_cli(args)
        return ex.value.code, stdout.getvalue(), stderr.getvalue()

    def test_no_args(self):
        exit_code, stdout, stderr = self._capture_create_cli([])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_GITOPSCLI_HELP, stderr)

    def test_help(self):
        exit_code, stdout, stderr = self._capture_create_cli(["--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_GITOPSCLI_HELP, stdout)
        self.assertEqual("", stderr)

    def test_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_create_cli(["-h"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_GITOPSCLI_HELP, stdout)
        self.assertEqual("", stderr)

    def test_add_pr_comment_no_args(self):
        exit_code, stdout, stderr = self._capture_create_cli(["add-pr-comment"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_ADD_PR_COMMENT_NO_ARGS_ERROR, stderr)

    def test_add_pr_comment_help(self):
        exit_code, stdout, stderr = self._capture_create_cli(["add-pr-comment", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_ADD_PR_COMMENT_HELP, stdout)
        self.assertEqual("", stderr)

    def test_add_pr_comment_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_create_cli(["add-pr-comment", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_ADD_PR_COMMENT_HELP, stdout)
        self.assertEqual("", stderr)

    def test_add_pr_comment_required_args(self):
        cli = create_cli(
            [
                "add-pr-comment",
                "--username",
                "USER",
                "--password",
                "PASS",
                "--organisation",
                "ORG",
                "--repository-name",
                "REPO",
                "--pr-id",
                "4711",
                "--text",
                "TEXT",
            ]
        )
        self.assertEqual(cli.command, "add-pr-comment")

        self.assertEqual(cli.username, "USER")
        self.assertEqual(cli.password, "PASS")
        self.assertEqual(cli.organisation, "ORG")
        self.assertEqual(cli.repository_name, "REPO")
        self.assertEqual(cli.pr_id, 4711)
        self.assertEqual(cli.text, "TEXT")

        self.assertIsNone(cli.parent_id)
        self.assertIsNone(cli.git_provider)
        self.assertIsNone(cli.git_provider_url)
        self.assertFalse(cli.verbose)

    def test_add_pr_comment_all_args(self):
        cli = create_cli(
            [
                "add-pr-comment",
                "--username",
                "USER",
                "--password",
                "PASS",
                "--git-provider",
                "GIT_PROVIDER",
                "--git-provider-url",
                "GIT_PROVIDER_URL",
                "--organisation",
                "ORG",
                "--repository-name",
                "REPO",
                "--pr-id",
                "4711",
                "--parent-id",
                "42",
                "--text",
                "TEXT",
                "--verbose",
            ]
        )
        self.assertEqual(cli.command, "add-pr-comment")

        self.assertEqual(cli.username, "USER")
        self.assertEqual(cli.password, "PASS")
        self.assertEqual(cli.git_provider, "GIT_PROVIDER")
        self.assertEqual(cli.git_provider_url, "GIT_PROVIDER_URL")
        self.assertEqual(cli.organisation, "ORG")
        self.assertEqual(cli.repository_name, "REPO")
        self.assertEqual(cli.pr_id, 4711)
        self.assertEqual(cli.parent_id, 42)
        self.assertEqual(cli.text, "TEXT")
        self.assertTrue(cli.verbose)

    def test_create_preview_no_args(self):
        exit_code, stdout, stderr = self._capture_create_cli(["create-preview"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_CREATE_PREVIEW_NO_ARGS_ERROR, stderr)

    def test_create_preview_help(self):
        exit_code, stdout, stderr = self._capture_create_cli(["create-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_CREATE_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_create_preview_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_create_cli(["create-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_CREATE_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_create_preview_required_args(self):
        cli = create_cli(
            [
                "create-preview",
                "--username",
                "USER",
                "--password",
                "PASS",
                "--git-user",
                "GIT_USER",
                "--git-email",
                "GIT_EMAIL",
                "--organisation",
                "ORG",
                "--repository-name",
                "REPO",
                "--pr-id",
                "4711",
            ]
        )
        self.assertEqual(cli.command, "create-preview")

        self.assertEqual(cli.username, "USER")
        self.assertEqual(cli.password, "PASS")
        self.assertEqual(cli.git_user, "GIT_USER")
        self.assertEqual(cli.git_email, "GIT_EMAIL")
        self.assertEqual(cli.organisation, "ORG")
        self.assertEqual(cli.repository_name, "REPO")
        self.assertEqual(cli.pr_id, 4711)

        self.assertIsNone(cli.git_provider)
        self.assertIsNone(cli.git_provider_url)
        self.assertIsNone(cli.parent_id)
        self.assertFalse(cli.create_pr)
        self.assertFalse(cli.auto_merge)
        self.assertFalse(cli.verbose)

    def test_create_preview_all_args(self):
        cli = create_cli(
            [
                "create-preview",
                "--username",
                "USER",
                "--password",
                "PASS",
                "--git-user",
                "GIT_USER",
                "--git-email",
                "GIT_EMAIL",
                "--git-provider",
                "GIT_PROVIDER",
                "--git-provider-url",
                "GIT_PROVIDER_URL",
                "--organisation",
                "ORG",
                "--repository-name",
                "REPO",
                "--pr-id",
                "4711",
                "--parent-id",
                "42",
                "--create-pr",
                "yEs",
                "--auto-merge",
                "1",
                "-v",
            ]
        )
        self.assertEqual(cli.command, "create-preview")

        self.assertEqual(cli.username, "USER")
        self.assertEqual(cli.password, "PASS")
        self.assertEqual(cli.git_user, "GIT_USER")
        self.assertEqual(cli.git_email, "GIT_EMAIL")
        self.assertEqual(cli.organisation, "ORG")
        self.assertEqual(cli.repository_name, "REPO")
        self.assertEqual(cli.pr_id, 4711)
        self.assertEqual(cli.parent_id, 42)

        self.assertEqual(cli.git_provider, "GIT_PROVIDER")
        self.assertEqual(cli.git_provider_url, "GIT_PROVIDER_URL")
        self.assertTrue(cli.create_pr)
        self.assertTrue(cli.auto_merge)
        self.assertTrue(cli.verbose)

    def test_delete_preview_no_args(self):
        exit_code, stdout, stderr = self._capture_create_cli(["delete-preview"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_DELETE_PREVIEW_NO_ARGS_ERROR, stderr)

    def test_delete_preview_help(self):
        exit_code, stdout, stderr = self._capture_create_cli(["delete-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_DELETE_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_delete_preview_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_create_cli(["delete-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_DELETE_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_delete_preview_required_args(self):
        cli = create_cli(
            [
                "delete-preview",
                "--username",
                "USER",
                "--password",
                "PASS",
                "--git-user",
                "GIT_USER",
                "--git-email",
                "GIT_EMAIL",
                "--organisation",
                "ORG",
                "--repository-name",
                "REPO",
                "--branch",
                "BRANCH",
            ]
        )
        self.assertEqual(cli.command, "delete-preview")

        self.assertEqual(cli.username, "USER")
        self.assertEqual(cli.password, "PASS")
        self.assertEqual(cli.git_user, "GIT_USER")
        self.assertEqual(cli.git_email, "GIT_EMAIL")
        self.assertEqual(cli.organisation, "ORG")
        self.assertEqual(cli.repository_name, "REPO")
        self.assertEqual(cli.branch, "BRANCH")

        self.assertIsNone(cli.git_provider)
        self.assertIsNone(cli.git_provider_url)
        self.assertFalse(cli.create_pr)
        self.assertFalse(cli.auto_merge)
        self.assertFalse(cli.verbose)

    def test_delete_preview_all_args(self):
        cli = create_cli(
            [
                "delete-preview",
                "--username",
                "USER",
                "--password",
                "PASS",
                "--git-user",
                "GIT_USER",
                "--git-email",
                "GIT_EMAIL",
                "--git-provider",
                "GIT_PROVIDER",
                "--git-provider-url",
                "GIT_PROVIDER_URL",
                "--organisation",
                "ORG",
                "--repository-name",
                "REPO",
                "--branch",
                "BRANCH",
                "--create-pr",
                "tRue",
                "--auto-merge",
                "y",
                "-v",
                "n",
            ]
        )
        self.assertEqual(cli.command, "delete-preview")

        self.assertEqual(cli.username, "USER")
        self.assertEqual(cli.password, "PASS")
        self.assertEqual(cli.git_user, "GIT_USER")
        self.assertEqual(cli.git_email, "GIT_EMAIL")
        self.assertEqual(cli.organisation, "ORG")
        self.assertEqual(cli.repository_name, "REPO")
        self.assertEqual(cli.branch, "BRANCH")

        self.assertEqual(cli.git_provider, "GIT_PROVIDER")
        self.assertEqual(cli.git_provider_url, "GIT_PROVIDER_URL")
        self.assertTrue(cli.create_pr)
        self.assertTrue(cli.auto_merge)
        self.assertFalse(cli.verbose)

    def test_deploy_no_args(self):
        exit_code, stdout, stderr = self._capture_create_cli(["deploy"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_DEPLOY_NO_ARGS_ERROR, stderr)

    def test_deploy_help(self):
        exit_code, stdout, stderr = self._capture_create_cli(["deploy", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_DEPLOY_HELP, stdout)
        self.assertEqual("", stderr)

    def test_deploy_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_create_cli(["deploy", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_DEPLOY_HELP, stdout)
        self.assertEqual("", stderr)

    def test_deploy_required_args(self):
        cli = create_cli(
            [
                "deploy",
                "--username",
                "USER",
                "--password",
                "PASS",
                "--git-user",
                "GIT_USER",
                "--git-email",
                "GIT_EMAIL",
                "--organisation",
                "ORG",
                "--repository-name",
                "REPO",
                "--file",
                "FILE",
                "--values",
                '{"a.b": 42}',  # json
            ]
        )
        self.assertEqual(cli.command, "deploy")

        self.assertEqual(cli.username, "USER")
        self.assertEqual(cli.password, "PASS")
        self.assertEqual(cli.git_user, "GIT_USER")
        self.assertEqual(cli.git_email, "GIT_EMAIL")
        self.assertEqual(cli.organisation, "ORG")
        self.assertEqual(cli.repository_name, "REPO")
        self.assertEqual(cli.file, "FILE")
        self.assertEqual(cli.values, {"a.b": 42})

        self.assertIsNone(cli.git_provider)
        self.assertIsNone(cli.git_provider_url)
        self.assertFalse(cli.create_pr)
        self.assertFalse(cli.auto_merge)
        self.assertFalse(cli.single_commit)
        self.assertFalse(cli.verbose)

    def test_deploy_all_args(self):
        cli = create_cli(
            [
                "deploy",
                "--username",
                "USER",
                "--password",
                "PASS",
                "--git-user",
                "GIT_USER",
                "--git-email",
                "GIT_EMAIL",
                "--git-provider",
                "GIT_PROVIDER",
                "--git-provider-url",
                "GIT_PROVIDER_URL",
                "--organisation",
                "ORG",
                "--repository-name",
                "REPO",
                "--file",
                "FILE",
                "--values",
                "{a.b: 42}",  # yaml
                "--create-pr",
                "--auto-merge",
                "--single-commit",
                "--verbose",
            ]
        )
        self.assertEqual(cli.command, "deploy")

        self.assertEqual(cli.username, "USER")
        self.assertEqual(cli.password, "PASS")
        self.assertEqual(cli.git_user, "GIT_USER")
        self.assertEqual(cli.git_email, "GIT_EMAIL")
        self.assertEqual(cli.organisation, "ORG")
        self.assertEqual(cli.repository_name, "REPO")
        self.assertEqual(cli.file, "FILE")
        self.assertEqual(cli.values, {"a.b": 42})

        self.assertEqual(cli.git_provider, "GIT_PROVIDER")
        self.assertEqual(cli.git_provider_url, "GIT_PROVIDER_URL")
        self.assertTrue(cli.create_pr)
        self.assertTrue(cli.auto_merge)
        self.assertTrue(cli.single_commit)
        self.assertTrue(cli.verbose)

    def test_sync_apps_no_args(self):
        exit_code, stdout, stderr = self._capture_create_cli(["sync-apps"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_SYNC_APPS_NO_ARGS_ERROR, stderr)

    def test_sync_apps_help(self):
        exit_code, stdout, stderr = self._capture_create_cli(["sync-apps", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_SYNC_APPS_HELP, stdout)
        self.assertEqual("", stderr)

    def test_sync_apps_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_create_cli(["sync-apps", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_SYNC_APPS_HELP, stdout)
        self.assertEqual("", stderr)

    def test_sync_apps_required_args(self):
        cli = create_cli(
            [
                "sync-apps",
                "--username",
                "USER",
                "--password",
                "PASS",
                "--git-user",
                "GIT_USER",
                "--git-email",
                "GIT_EMAIL",
                "--organisation",
                "ORG",
                "--repository-name",
                "REPO",
                "--root-organisation",
                "ROOT_ORGA",
                "--root-repository-name",
                "ROOT_REPO",
            ]
        )
        self.assertEqual(cli.command, "sync-apps")

        self.assertEqual(cli.username, "USER")
        self.assertEqual(cli.password, "PASS")
        self.assertEqual(cli.git_user, "GIT_USER")
        self.assertEqual(cli.git_email, "GIT_EMAIL")
        self.assertEqual(cli.organisation, "ORG")
        self.assertEqual(cli.repository_name, "REPO")
        self.assertEqual(cli.root_organisation, "ROOT_ORGA")
        self.assertEqual(cli.root_repository_name, "ROOT_REPO")

        self.assertIsNone(cli.git_provider)
        self.assertIsNone(cli.git_provider_url)
        self.assertFalse(cli.verbose)

    def test_sync_apps_all_args(self):
        cli = create_cli(
            [
                "sync-apps",
                "--username",
                "USER",
                "--password",
                "PASS",
                "--git-user",
                "GIT_USER",
                "--git-email",
                "GIT_EMAIL",
                "--git-provider",
                "GIT_PROVIDER",
                "--git-provider-url",
                "GIT_PROVIDER_URL",
                "--organisation",
                "ORG",
                "--repository-name",
                "REPO",
                "--root-organisation",
                "ROOT_ORGA",
                "--root-repository-name",
                "ROOT_REPO",
                "--verbose",
            ]
        )
        self.assertEqual(cli.command, "sync-apps")

        self.assertEqual(cli.username, "USER")
        self.assertEqual(cli.password, "PASS")
        self.assertEqual(cli.git_user, "GIT_USER")
        self.assertEqual(cli.git_email, "GIT_EMAIL")
        self.assertEqual(cli.organisation, "ORG")
        self.assertEqual(cli.repository_name, "REPO")
        self.assertEqual(cli.root_organisation, "ROOT_ORGA")
        self.assertEqual(cli.root_repository_name, "ROOT_REPO")

        self.assertEqual(cli.git_provider, "GIT_PROVIDER")
        self.assertEqual(cli.git_provider_url, "GIT_PROVIDER_URL")
        self.assertTrue(cli.verbose)
