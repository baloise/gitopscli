import unittest
from unittest.mock import MagicMock, patch

from gitopscli.git import GitRepoApi
from gitopscli.git.git_repo_api_logging_proxy import GitRepoApiLoggingProxy


class GitRepoApiLoggingProxyTest(unittest.TestCase):
    def setUp(self):
        self.__mock_repo_api: GitRepoApi = MagicMock()
        self.__testee = GitRepoApiLoggingProxy(self.__mock_repo_api)

    def test_get_username(self):
        expected_return_value = "<username>"
        self.__mock_repo_api.get_username.return_value = expected_return_value

        actual_return_value = self.__testee.get_username()

        self.assertEqual(actual_return_value, expected_return_value)
        self.__mock_repo_api.get_username.assert_called_once_with()

    def test_get_password(self):
        expected_return_value = "<password>"
        self.__mock_repo_api.get_password.return_value = expected_return_value

        actual_return_value = self.__testee.get_password()

        self.assertEqual(actual_return_value, expected_return_value)
        self.__mock_repo_api.get_password.assert_called_once_with()

    def test_get_clone_url(self):
        expected_return_value = "<clone url>"
        self.__mock_repo_api.get_clone_url.return_value = expected_return_value

        actual_return_value = self.__testee.get_clone_url()

        self.assertEqual(actual_return_value, expected_return_value)
        self.__mock_repo_api.get_clone_url.assert_called_once_with()

    @patch("gitopscli.git.git_repo_api_logging_proxy.logging")
    def test_create_pull_request(self, logging_mock):
        expected_return_value = GitRepoApi.PullRequestIdAndUrl("<id>", "<url>")
        self.__mock_repo_api.create_pull_request.return_value = expected_return_value

        actual_return_value = self.__testee.create_pull_request(
            from_branch="<from branch>", to_branch="<to branch>", title="<title>", description="<description>"
        )

        self.assertEqual(actual_return_value, expected_return_value)
        self.__mock_repo_api.create_pull_request.assert_called_once_with(
            "<from branch>", "<to branch>", "<title>", "<description>"
        )
        logging_mock.info.assert_called_once_with(
            "Creating pull request from '%s' to '%s' with title: %s", "<from branch>", "<to branch>", "<title>",
        )

    @patch("gitopscli.git.git_repo_api_logging_proxy.logging")
    def test_merge_pull_request(self, logging_mock):
        self.__testee.merge_pull_request(pr_id="<pr_id>")
        self.__mock_repo_api.merge_pull_request.assert_called_once_with("<pr_id>")
        logging_mock.info.assert_called_once_with(
            "Merging pull request %s", "<pr_id>",
        )

    @patch("gitopscli.git.git_repo_api_logging_proxy.logging")
    def test_add_pull_request_comment(self, logging_mock):
        self.__testee.add_pull_request_comment(pr_id="<pr_id>", text="<text>", parent_id="<parent_id>")
        self.__mock_repo_api.add_pull_request_comment.assert_called_once_with("<pr_id>", "<text>", "<parent_id>")
        logging_mock.info.assert_called_once_with(
            "Creating comment for pull request %s as reply to comment %s with content: %s",
            "<pr_id>",
            "<parent_id>",
            "<text>",
        )

    @patch("gitopscli.git.git_repo_api_logging_proxy.logging")
    def test_add_pull_request_comment_without_parent_id(self, logging_mock):
        self.__testee.add_pull_request_comment(pr_id="<pr_id>", text="<text>", parent_id=None)
        self.__mock_repo_api.add_pull_request_comment.assert_called_once_with("<pr_id>", "<text>", None)
        logging_mock.info.assert_called_once_with(
            "Creating comment for pull request %s with content: %s", "<pr_id>", "<text>",
        )

    @patch("gitopscli.git.git_repo_api_logging_proxy.logging")
    def test_delete_branch(self, logging_mock):
        self.__testee.delete_branch("<branch>")
        self.__mock_repo_api.delete_branch.assert_called_once_with("<branch>")
        logging_mock.info.assert_called_once_with(
            "Deleting branch '%s'", "<branch>",
        )

    def test_get_branch_head_hash(self):
        expected_return_value = "<hash>"
        self.__mock_repo_api.get_branch_head_hash.return_value = expected_return_value

        actual_return_value = self.__testee.get_branch_head_hash("<branch>")

        self.assertEqual(actual_return_value, expected_return_value)
        self.__mock_repo_api.get_branch_head_hash.assert_called_once_with("<branch>")

    def test_get_pull_request_branch(self):
        expected_return_value = "<hash>"
        self.__mock_repo_api.get_pull_request_branch.return_value = expected_return_value

        actual_return_value = self.__testee.get_pull_request_branch("<pr_id>")

        self.assertEqual(actual_return_value, expected_return_value)
        self.__mock_repo_api.get_pull_request_branch.assert_called_once_with("<pr_id>")
