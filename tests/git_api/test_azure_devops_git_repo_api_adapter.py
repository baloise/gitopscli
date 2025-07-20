import unittest
from unittest.mock import MagicMock, patch

import pytest
from msrest.exceptions import ClientException

from gitopscli.git_api.azure_devops_git_repo_api_adapter import AzureDevOpsGitRepoApiAdapter
from gitopscli.gitops_exception import GitOpsException


class AzureDevOpsGitRepoApiAdapterTest(unittest.TestCase):
    def setUp(self):
        with patch("gitopscli.git_api.azure_devops_git_repo_api_adapter.Connection"):
            self.adapter = AzureDevOpsGitRepoApiAdapter(
                git_provider_url="https://dev.azure.com/testorg",
                username="testuser",
                password="testtoken",
                organisation="testproject",
                repository_name="testrepo",
            )

    @patch("gitopscli.git_api.azure_devops_git_repo_api_adapter.Connection")
    def test_init_success(self, mock_connection):
        mock_git_client = MagicMock()
        mock_connection.return_value.clients.get_git_client.return_value = mock_git_client

        adapter = AzureDevOpsGitRepoApiAdapter(
            git_provider_url="https://dev.azure.com/myorg",
            username="user",
            password="token",
            organisation="project",
            repository_name="repo",
        )

        self.assertEqual(adapter.get_username(), "user")
        self.assertEqual(adapter.get_password(), "token")
        self.assertEqual(adapter.get_clone_url(), "https://dev.azure.com/myorg/project/_git/repo")

    def test_init_no_password_raises_exception(self):
        with pytest.raises(GitOpsException) as context:
            AzureDevOpsGitRepoApiAdapter(
                git_provider_url="https://dev.azure.com/org",
                username="user",
                password=None,
                organisation="project",
                repository_name="repo",
            )
        self.assertEqual(str(context.value), "Password (Personal Access Token) is required for Azure DevOps")

    def test_get_clone_url(self):
        expected_url = "https://dev.azure.com/testorg/testproject/_git/testrepo"
        self.assertEqual(self.adapter.get_clone_url(), expected_url)

    def test_create_pull_request_success(self):
        mock_pr = MagicMock()
        mock_pr.pull_request_id = 123
        mock_pr.url = "https://dev.azure.com/testorg/testproject/_git/testrepo/pullrequest/123"

        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_pull_request.return_value = mock_pr

        result = self.adapter.create_pull_request(
            from_branch="feature-branch", to_branch="main", title="Test PR", description="Test description"
        )

        self.assertEqual(result.pr_id, 123)
        self.assertEqual(result.url, "https://dev.azure.com/testorg/testproject/_git/testrepo/pullrequest/123")

        # Verify the git client was called correctly
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_pull_request.assert_called_once()
        call_args = self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_pull_request.call_args
        self.assertEqual(call_args.kwargs["repository_id"], "testrepo")
        self.assertEqual(call_args.kwargs["project"], "testproject")

        pr_request = call_args.kwargs["git_pull_request_to_create"]
        self.assertEqual(pr_request.source_ref_name, "refs/heads/feature-branch")
        self.assertEqual(pr_request.target_ref_name, "refs/heads/main")
        self.assertEqual(pr_request.title, "Test PR")
        self.assertEqual(pr_request.description, "Test description")

    def test_create_pull_request_with_refs_prefix(self):
        mock_pr = MagicMock()
        mock_pr.pull_request_id = 123
        mock_pr.url = "test-url"

        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_pull_request.return_value = mock_pr

        self.adapter.create_pull_request(
            from_branch="refs/heads/feature-branch",
            to_branch="refs/heads/main",
            title="Test PR",
            description="Test description",
        )

        # Verify the git client was called correctly with refs already included
        call_args = self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_pull_request.call_args
        pr_request = call_args.kwargs["git_pull_request_to_create"]
        self.assertEqual(pr_request.source_ref_name, "refs/heads/feature-branch")
        self.assertEqual(pr_request.target_ref_name, "refs/heads/main")

    def test_create_pull_request_unauthorized(self):
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_pull_request.side_effect = ClientException("401")

        with pytest.raises(GitOpsException) as context:
            self.adapter.create_pull_request("from", "to", "title", "desc")

        self.assertEqual(str(context.value), "Bad credentials")

    def test_create_pull_request_not_found(self):
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_pull_request.side_effect = ClientException("404")

        with pytest.raises(GitOpsException) as context:
            self.adapter.create_pull_request("from", "to", "title", "desc")

        self.assertEqual(str(context.value), "Repository 'testproject/testrepo' does not exist")

    def test_create_pull_request_to_default_branch(self):
        # Mock get repository for default branch
        mock_repo = MagicMock()
        mock_repo.default_branch = "refs/heads/develop"
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_repository.return_value = mock_repo

        # Mock create pull request
        mock_pr = MagicMock()
        mock_pr.pull_request_id = 456
        mock_pr.url = "test-url"
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_pull_request.return_value = mock_pr

        result = self.adapter.create_pull_request_to_default_branch(
            from_branch="feature", title="Test PR", description="Test desc"
        )

        self.assertEqual(result.pr_id, 456)

        # Verify create PR was called with default branch
        call_args = self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_pull_request.call_args
        pr_request = call_args.kwargs["git_pull_request_to_create"]
        self.assertEqual(pr_request.source_ref_name, "refs/heads/feature")
        self.assertEqual(pr_request.target_ref_name, "refs/heads/develop")

    def test_merge_pull_request_success(self):
        # Mock get pull request
        mock_pr = MagicMock()
        mock_pr.last_merge_source_commit = MagicMock()
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_pull_request.return_value = mock_pr

        # Mock update pull request
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.update_pull_request.return_value = None

        self.adapter.merge_pull_request(123, "squash")

        # Verify get_pull_request was called
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_pull_request.assert_called_once_with(
            repository_id="testrepo", pull_request_id=123, project="testproject"
        )

        # Verify update_pull_request was called
        call_args = self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.update_pull_request.call_args
        self.assertEqual(call_args.kwargs["repository_id"], "testrepo")
        self.assertEqual(call_args.kwargs["pull_request_id"], 123)
        self.assertEqual(call_args.kwargs["project"], "testproject")

        pr_update = call_args.kwargs["git_pull_request_to_update"]
        self.assertEqual(pr_update.status, "completed")
        self.assertEqual(pr_update.completion_options.merge_strategy, "squash")

    def test_merge_pull_request_different_strategies(self):
        # Mock get pull request
        mock_pr = MagicMock()
        mock_pr.last_merge_source_commit = MagicMock()
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_pull_request.return_value = mock_pr

        # Test merge strategy
        self.adapter.merge_pull_request(123, "merge")
        call_args = self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.update_pull_request.call_args
        pr_update = call_args.kwargs["git_pull_request_to_update"]
        self.assertEqual(pr_update.completion_options.merge_strategy, "noFastForward")

        # Test rebase strategy
        self.adapter.merge_pull_request(456, "rebase")
        call_args = self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.update_pull_request.call_args
        pr_update = call_args.kwargs["git_pull_request_to_update"]
        self.assertEqual(pr_update.completion_options.merge_strategy, "rebase")

    def test_add_pull_request_comment_success(self):
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_thread.return_value = None

        self.adapter.add_pull_request_comment(123, "Test comment")

        # Verify create_thread was called
        call_args = self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_thread.call_args
        self.assertEqual(call_args.kwargs["repository_id"], "testrepo")
        self.assertEqual(call_args.kwargs["pull_request_id"], 123)
        self.assertEqual(call_args.kwargs["project"], "testproject")

        thread = call_args.kwargs["comment_thread"]
        self.assertEqual(len(thread.comments), 1)
        self.assertEqual(thread.comments[0].content, "Test comment")
        self.assertEqual(thread.comments[0].comment_type, "text")
        self.assertEqual(thread.status, "active")

    def test_get_branch_head_hash_success(self):
        mock_ref = MagicMock()
        mock_ref.object_id = "abc123def456"
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_refs.return_value = [mock_ref]

        result = self.adapter.get_branch_head_hash("main")

        self.assertEqual(result, "abc123def456")
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_refs.assert_called_once_with(
            repository_id="testrepo", project="testproject", filter="heads/main"
        )

    def test_get_branch_head_hash_not_found(self):
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_refs.return_value = []

        with pytest.raises(GitOpsException) as context:
            self.adapter.get_branch_head_hash("nonexistent")

        self.assertEqual(str(context.value), "Branch 'nonexistent' does not exist")

    def test_get_pull_request_branch_success(self):
        mock_pr = MagicMock()
        mock_pr.source_ref_name = "refs/heads/feature-branch"
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_pull_request.return_value = mock_pr

        result = self.adapter.get_pull_request_branch(123)

        self.assertEqual(result, "feature-branch")
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_pull_request.assert_called_once_with(
            repository_id="testrepo", pull_request_id=123, project="testproject"
        )

    def test_get_pull_request_branch_without_refs_prefix(self):
        mock_pr = MagicMock()
        mock_pr.source_ref_name = "feature-branch"
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_pull_request.return_value = mock_pr

        result = self.adapter.get_pull_request_branch(123)

        self.assertEqual(result, "feature-branch")

    def test_delete_branch_success(self):
        # Mock get refs
        mock_ref = MagicMock()
        mock_ref.object_id = "abc123def456"
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_refs.return_value = [mock_ref]

        # Mock update refs
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.update_refs.return_value = None

        self.adapter.delete_branch("feature-branch")

        # Verify get_refs was called
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_refs.assert_called_once_with(
            repository_id="testrepo", project="testproject", filter="heads/feature-branch"
        )

        # Verify update_refs was called
        call_args = self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.update_refs.call_args
        self.assertEqual(call_args.kwargs["repository_id"], "testrepo")
        self.assertEqual(call_args.kwargs["project"], "testproject")

        ref_updates = call_args.kwargs["ref_updates"]
        self.assertEqual(len(ref_updates), 1)
        self.assertEqual(ref_updates[0].name, "refs/heads/feature-branch")
        self.assertEqual(ref_updates[0].old_object_id, "abc123def456")
        self.assertEqual(ref_updates[0].new_object_id, "0000000000000000000000000000000000000000")

    def test_delete_branch_not_found(self):
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_refs.return_value = []

        with pytest.raises(GitOpsException) as context:
            self.adapter.delete_branch("nonexistent")

        self.assertEqual(str(context.value), "Branch 'nonexistent' does not exist")

    def test_add_pull_request_label_does_nothing(self):
        # Labels aren't supported in the SDK implementation, should not raise exception
        try:
            self.adapter.add_pull_request_label(123, ["bug", "enhancement"])
        except Exception as ex:  # noqa: BLE001
            self.fail(f"add_pull_request_label should not raise exception: {ex}")

    def test_username_and_password_getters(self):
        self.assertEqual(self.adapter.get_username(), "testuser")
        self.assertEqual(self.adapter.get_password(), "testtoken")

    def test_connection_error_handling(self):
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.create_pull_request.side_effect = Exception(
            "Connection failed"
        )

        with pytest.raises(GitOpsException) as context:
            self.adapter.create_pull_request("from", "to", "title", "desc")

        self.assertIn("Error connecting to 'https://dev.azure.com/testorg'", str(context.value))

    def test_get_default_branch_success(self):
        mock_repo = MagicMock()
        mock_repo.default_branch = "refs/heads/main"
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_repository.return_value = mock_repo

        result = self.adapter._AzureDevOpsGitRepoApiAdapter__get_default_branch()

        self.assertEqual(result, "main")
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_repository.assert_called_once_with(
            repository_id="testrepo", project="testproject"
        )

    def test_get_default_branch_fallback(self):
        mock_repo = MagicMock()
        mock_repo.default_branch = None
        self.adapter._AzureDevOpsGitRepoApiAdapter__git_client.get_repository.return_value = mock_repo

        result = self.adapter._AzureDevOpsGitRepoApiAdapter__get_default_branch()

        self.assertEqual(result, "main")  # Should fallback to "main"


if __name__ == "__main__":
    unittest.main()
