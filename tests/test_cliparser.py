import os
import sys
import unittest
from contextlib import contextmanager
from io import StringIO
import pytest

from gitopscli.commands import (
    DeployCommand,
    SyncAppsCommand,
    AddPrCommentCommand,
    CreatePreviewCommand,
    CreatePrPreviewCommand,
    DeletePreviewCommand,
    DeletePrPreviewCommand,
    VersionCommand,
)
from gitopscli.cliparser import parse_args

EXPECTED_GITOPSCLI_HELP = """\
usage: gitopscli [-h]
                 {deploy,sync-apps,add-pr-comment,create-preview,create-pr-preview,delete-preview,delete-pr-preview,version}
                 ...

GitOps CLI

optional arguments:
  -h, --help            show this help message and exit

commands:
  {deploy,sync-apps,add-pr-comment,create-preview,create-pr-preview,delete-preview,delete-pr-preview,version}
    deploy              Trigger a new deployment by changing YAML values
    sync-apps           Synchronize applications (= every directory) from apps
                        config repository to apps root config
    add-pr-comment      Create a comment on the pull request
    create-preview      Create a preview environment
    create-pr-preview   Create a preview environment
    delete-preview      Delete a preview environment
    delete-pr-preview   Delete a pr preview environment
    version             Show the GitOps CLI version information
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
                                --git-hash GIT_HASH --preview-id PREVIEW_ID
                                [-v [VERBOSE]]
gitopscli create-preview: error: the following arguments are required: --username, --password, --organisation, --repository-name, --git-hash, --preview-id
"""
EXPECTED_CREATE_PR_PREVIEW_NO_ARGS_ERROR = """\
usage: gitopscli create-pr-preview [-h] --username USERNAME --password
                                   PASSWORD [--git-user GIT_USER]
                                   [--git-email GIT_EMAIL] --organisation
                                   ORGANISATION --repository-name
                                   REPOSITORY_NAME
                                   [--git-provider GIT_PROVIDER]
                                   [--git-provider-url GIT_PROVIDER_URL]
                                   --pr-id PR_ID [--parent-id PARENT_ID]
                                   [-v [VERBOSE]]
gitopscli create-pr-preview: error: the following arguments are required: --username, --password, --organisation, --repository-name, --pr-id
"""

EXPECTED_CREATE_PREVIEW_HELP = """\
usage: gitopscli create-preview [-h] --username USERNAME --password PASSWORD
                                [--git-user GIT_USER] [--git-email GIT_EMAIL]
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL]
                                --git-hash GIT_HASH --preview-id PREVIEW_ID
                                [-v [VERBOSE]]

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
  --git-hash GIT_HASH   the git hash which should be deployed
  --preview-id PREVIEW_ID
                        the id of folder in the config repo which will be
                        created
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
"""

EXPECTED_CREATE_PR_PREVIEW_HELP = """\
usage: gitopscli create-pr-preview [-h] --username USERNAME --password
                                   PASSWORD [--git-user GIT_USER]
                                   [--git-email GIT_EMAIL] --organisation
                                   ORGANISATION --repository-name
                                   REPOSITORY_NAME
                                   [--git-provider GIT_PROVIDER]
                                   [--git-provider-url GIT_PROVIDER_URL]
                                   --pr-id PR_ID [--parent-id PARENT_ID]
                                   [-v [VERBOSE]]

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
                                [--git-provider-url GIT_PROVIDER_URL]
                                --preview-id PREVIEW_ID
                                [--expect-preview-exists [EXPECT_PREVIEW_EXISTS]]
                                [-v [VERBOSE]]
gitopscli delete-preview: error: the following arguments are required: --username, --password, --organisation, --repository-name, --preview-id
"""

EXPECTED_DELETE_PR_PREVIEW_NO_ARGS_ERROR = """\
usage: gitopscli delete-pr-preview [-h] --username USERNAME --password
                                   PASSWORD [--git-user GIT_USER]
                                   [--git-email GIT_EMAIL] --organisation
                                   ORGANISATION --repository-name
                                   REPOSITORY_NAME
                                   [--git-provider GIT_PROVIDER]
                                   [--git-provider-url GIT_PROVIDER_URL]
                                   --branch BRANCH
                                   [--expect-preview-exists [EXPECT_PREVIEW_EXISTS]]
                                   [-v [VERBOSE]]
gitopscli delete-pr-preview: error: the following arguments are required: --username, --password, --organisation, --repository-name, --branch
"""

EXPECTED_DELETE_PREVIEW_HELP = """\
usage: gitopscli delete-preview [-h] --username USERNAME --password PASSWORD
                                [--git-user GIT_USER] [--git-email GIT_EMAIL]
                                --organisation ORGANISATION --repository-name
                                REPOSITORY_NAME [--git-provider GIT_PROVIDER]
                                [--git-provider-url GIT_PROVIDER_URL]
                                --preview-id PREVIEW_ID
                                [--expect-preview-exists [EXPECT_PREVIEW_EXISTS]]
                                [-v [VERBOSE]]

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
  --preview-id PREVIEW_ID
                        The preview-id for which the preview was created for
  --expect-preview-exists [EXPECT_PREVIEW_EXISTS]
                        Fail if preview does not exist
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
"""

EXPECTED_DELETE_PR_PREVIEW_HELP = """\
usage: gitopscli delete-pr-preview [-h] --username USERNAME --password
                                   PASSWORD [--git-user GIT_USER]
                                   [--git-email GIT_EMAIL] --organisation
                                   ORGANISATION --repository-name
                                   REPOSITORY_NAME
                                   [--git-provider GIT_PROVIDER]
                                   [--git-provider-url GIT_PROVIDER_URL]
                                   --branch BRANCH
                                   [--expect-preview-exists [EXPECT_PREVIEW_EXISTS]]
                                   [-v [VERBOSE]]

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
  --expect-preview-exists [EXPECT_PREVIEW_EXISTS]
                        Fail if preview does not exist
  -v [VERBOSE], --verbose [VERBOSE]
                        Verbose exception logging
"""

EXPECTED_DEPLOY_NO_ARGS_ERROR = """\
usage: gitopscli deploy [-h] --file FILE --values VALUES
                        [--single-commit [SINGLE_COMMIT]]
                        [--commit-message COMMIT_MESSAGE] --username USERNAME
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
                        [--single-commit [SINGLE_COMMIT]]
                        [--commit-message COMMIT_MESSAGE] --username USERNAME
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
  --commit-message COMMIT_MESSAGE
                        Specify exact commit message of deployment commit
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

EXPECTED_VERSION_HELP = """\
usage: gitopscli version [-h]

optional arguments:
  -h, --help  show this help message and exit
"""


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    old_environ = dict(os.environ)
    os.environ["COLUMNS"] = "80"
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err
        os.environ.clear()
        os.environ.update(old_environ)


class CliParserTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maxDiff = None

    @staticmethod
    def _capture_parse_args(args):
        with captured_output() as (stdout, stderr), pytest.raises(SystemExit) as ex:
            parse_args(args)
        return ex.value.code, stdout.getvalue(), stderr.getvalue()

    def assertType(self, o: object, t: type):
        self.assertTrue(isinstance(o, t))

    def test_no_args(self):
        exit_code, stdout, stderr = self._capture_parse_args([])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_GITOPSCLI_HELP, stderr)

    def test_help(self):
        exit_code, stdout, stderr = self._capture_parse_args(["--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_GITOPSCLI_HELP, stdout)
        self.assertEqual("", stderr)

    def test_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_parse_args(["-h"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_GITOPSCLI_HELP, stdout)
        self.assertEqual("", stderr)

    def test_add_pr_comment_no_args(self):
        exit_code, stdout, stderr = self._capture_parse_args(["add-pr-comment"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_ADD_PR_COMMENT_NO_ARGS_ERROR, stderr)

    def test_add_pr_comment_help(self):
        exit_code, stdout, stderr = self._capture_parse_args(["add-pr-comment", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_ADD_PR_COMMENT_HELP, stdout)
        self.assertEqual("", stderr)

    def test_add_pr_comment_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_parse_args(["add-pr-comment", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_ADD_PR_COMMENT_HELP, stdout)
        self.assertEqual("", stderr)

    def test_add_pr_comment_required_args(self):
        verbose, args = parse_args(
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
        self.assertType(args, AddPrCommentCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.pr_id, 4711)
        self.assertEqual(args.text, "TEXT")

        self.assertIsNone(args.parent_id)
        self.assertIsNone(args.git_provider)
        self.assertIsNone(args.git_provider_url)
        self.assertFalse(verbose)

    def test_add_pr_comment_all_args(self):
        verbose, args = parse_args(
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
        self.assertType(args, AddPrCommentCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_provider, "GIT_PROVIDER")
        self.assertEqual(args.git_provider_url, "GIT_PROVIDER_URL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.pr_id, 4711)
        self.assertEqual(args.parent_id, 42)
        self.assertEqual(args.text, "TEXT")
        self.assertTrue(verbose)

    def test_create_preview_no_args(self):
        exit_code, stdout, stderr = self._capture_parse_args(["create-preview"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_CREATE_PREVIEW_NO_ARGS_ERROR, stderr)

    def test_create_preview_help(self):
        exit_code, stdout, stderr = self._capture_parse_args(["create-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_CREATE_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_create_preview_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_parse_args(["create-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_CREATE_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_create_preview_required_args(self):
        verbose, args = parse_args(
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
                "--git-hash",
                "c0784a34e834117e1489973327ff4ff3c2582b94",
                "--preview-id",
                "abc123",
            ]
        )
        self.assertType(args, CreatePreviewCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.git_hash, "c0784a34e834117e1489973327ff4ff3c2582b94")
        self.assertEqual(args.preview_id, "abc123")

        self.assertIsNone(args.git_provider)
        self.assertIsNone(args.git_provider_url)
        self.assertFalse(verbose)

    def test_create_preview_all_args(self):
        verbose, args = parse_args(
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
                "--git-hash",
                "c0784a34e834117e1489973327ff4ff3c2582b94",
                "--preview-id",
                "abc123",
                "-v",
            ]
        )
        self.assertType(args, CreatePreviewCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.git_hash, "c0784a34e834117e1489973327ff4ff3c2582b94")
        self.assertEqual(args.preview_id, "abc123")

        self.assertEqual(args.git_provider, "GIT_PROVIDER")
        self.assertEqual(args.git_provider_url, "GIT_PROVIDER_URL")
        self.assertTrue(verbose)

    def test_create_pr_preview_no_args(self):
        exit_code, stdout, stderr = self._capture_parse_args(["create-pr-preview"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_CREATE_PR_PREVIEW_NO_ARGS_ERROR, stderr)

    def test_create_pr_preview_help(self):
        exit_code, stdout, stderr = self._capture_parse_args(["create-pr-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_CREATE_PR_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_create_pr_preview_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_parse_args(["create-pr-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_CREATE_PR_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_create_pr_preview_required_args(self):
        verbose, args = parse_args(
            [
                "create-pr-preview",
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
        self.assertType(args, CreatePrPreviewCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.pr_id, 4711)

        self.assertIsNone(args.git_provider)
        self.assertIsNone(args.git_provider_url)
        self.assertIsNone(args.parent_id)
        self.assertFalse(verbose)

    def test_create_pr_preview_all_args(self):
        verbose, args = parse_args(
            [
                "create-pr-preview",
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
                "-v",
            ]
        )
        self.assertType(args, CreatePrPreviewCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.pr_id, 4711)
        self.assertEqual(args.parent_id, 42)

        self.assertEqual(args.git_provider, "GIT_PROVIDER")
        self.assertEqual(args.git_provider_url, "GIT_PROVIDER_URL")
        self.assertTrue(verbose)

    def test_delete_preview_no_args(self):
        exit_code, stdout, stderr = self._capture_parse_args(["delete-preview"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_DELETE_PREVIEW_NO_ARGS_ERROR, stderr)

    def test_delete_preview_help(self):
        exit_code, stdout, stderr = self._capture_parse_args(["delete-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_DELETE_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_delete_preview_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_parse_args(["delete-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_DELETE_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_delete_preview_required_args(self):
        verbose, args = parse_args(
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
                "--preview-id",
                "abc123",
            ]
        )
        self.assertType(args, DeletePreviewCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.preview_id, "abc123")

        self.assertIsNone(args.git_provider)
        self.assertIsNone(args.git_provider_url)
        self.assertFalse(args.expect_preview_exists)
        self.assertFalse(verbose)

    def test_delete_preview_all_args(self):
        verbose, args = parse_args(
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
                "--preview-id",
                "abc123",
                "--expect-preview-exists",
                "-v",
                "n",
            ]
        )
        self.assertType(args, DeletePreviewCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.preview_id, "abc123")

        self.assertEqual(args.git_provider, "GIT_PROVIDER")
        self.assertEqual(args.git_provider_url, "GIT_PROVIDER_URL")
        self.assertTrue(args.expect_preview_exists)
        self.assertFalse(verbose)

    def test_delete_pr_preview_no_args(self):
        exit_code, stdout, stderr = self._capture_parse_args(["delete-pr-preview"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_DELETE_PR_PREVIEW_NO_ARGS_ERROR, stderr)

    def test_delete_pr_preview_help(self):
        exit_code, stdout, stderr = self._capture_parse_args(["delete-pr-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_DELETE_PR_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_delete_pr_preview_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_parse_args(["delete-pr-preview", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_DELETE_PR_PREVIEW_HELP, stdout)
        self.assertEqual("", stderr)

    def test_delete_pr_preview_required_args(self):
        verbose, args = parse_args(
            [
                "delete-pr-preview",
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
        self.assertType(args, DeletePrPreviewCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.branch, "BRANCH")

        self.assertIsNone(args.git_provider)
        self.assertIsNone(args.git_provider_url)
        self.assertFalse(args.expect_preview_exists)
        self.assertFalse(verbose)

    def test_delete_pr_preview_all_args(self):
        verbose, args = parse_args(
            [
                "delete-pr-preview",
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
                "--expect-preview-exists",
                "-v",
                "n",
            ]
        )
        self.assertType(args, DeletePrPreviewCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.branch, "BRANCH")

        self.assertEqual(args.git_provider, "GIT_PROVIDER")
        self.assertEqual(args.git_provider_url, "GIT_PROVIDER_URL")
        self.assertTrue(args.expect_preview_exists)
        self.assertFalse(verbose)

    def test_deploy_no_args(self):
        exit_code, stdout, stderr = self._capture_parse_args(["deploy"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_DEPLOY_NO_ARGS_ERROR, stderr)

    def test_deploy_help(self):
        exit_code, stdout, stderr = self._capture_parse_args(["deploy", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_DEPLOY_HELP, stdout)
        self.assertEqual("", stderr)

    def test_deploy_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_parse_args(["deploy", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_DEPLOY_HELP, stdout)
        self.assertEqual("", stderr)

    def test_deploy_required_args(self):
        verbose, args = parse_args(
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
        self.assertType(args, DeployCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.file, "FILE")
        self.assertEqual(args.values, {"a.b": 42})

        self.assertIsNone(args.git_provider)
        self.assertIsNone(args.git_provider_url)
        self.assertFalse(args.create_pr)
        self.assertFalse(args.auto_merge)
        self.assertFalse(args.single_commit)
        self.assertFalse(verbose)

    def test_deploy_all_args(self):
        verbose, args = parse_args(
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
        self.assertType(args, DeployCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.file, "FILE")
        self.assertEqual(args.values, {"a.b": 42})

        self.assertEqual(args.git_provider, "GIT_PROVIDER")
        self.assertEqual(args.git_provider_url, "GIT_PROVIDER_URL")
        self.assertTrue(args.create_pr)
        self.assertTrue(args.auto_merge)
        self.assertTrue(args.single_commit)
        self.assertTrue(verbose)

    def test_sync_apps_no_args(self):
        exit_code, stdout, stderr = self._capture_parse_args(["sync-apps"])
        self.assertEqual(exit_code, 2)
        self.assertEqual("", stdout)
        self.assertEqual(EXPECTED_SYNC_APPS_NO_ARGS_ERROR, stderr)

    def test_sync_apps_help(self):
        exit_code, stdout, stderr = self._capture_parse_args(["sync-apps", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_SYNC_APPS_HELP, stdout)
        self.assertEqual("", stderr)

    def test_sync_apps_help_shortcut(self):
        exit_code, stdout, stderr = self._capture_parse_args(["sync-apps", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_SYNC_APPS_HELP, stdout)
        self.assertEqual("", stderr)

    def test_sync_apps_required_args(self):
        verbose, args = parse_args(
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
        self.assertType(args, SyncAppsCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.root_organisation, "ROOT_ORGA")
        self.assertEqual(args.root_repository_name, "ROOT_REPO")

        self.assertIsNone(args.git_provider)
        self.assertIsNone(args.git_provider_url)
        self.assertFalse(verbose)

    def test_sync_apps_all_args(self):
        verbose, args = parse_args(
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
        self.assertType(args, SyncAppsCommand.Args)

        self.assertEqual(args.username, "USER")
        self.assertEqual(args.password, "PASS")
        self.assertEqual(args.git_user, "GIT_USER")
        self.assertEqual(args.git_email, "GIT_EMAIL")
        self.assertEqual(args.organisation, "ORG")
        self.assertEqual(args.repository_name, "REPO")
        self.assertEqual(args.root_organisation, "ROOT_ORGA")
        self.assertEqual(args.root_repository_name, "ROOT_REPO")

        self.assertEqual(args.git_provider, "GIT_PROVIDER")
        self.assertEqual(args.git_provider_url, "GIT_PROVIDER_URL")
        self.assertTrue(verbose)

    def test_version_args(self):
        verbose, args = parse_args(["version"])
        self.assertType(args, VersionCommand.Args)

    def test_version_help(self):
        exit_code, stdout, stderr = self._capture_parse_args(["version", "--help"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(EXPECTED_VERSION_HELP, stdout)
        self.assertEqual("", stderr)
