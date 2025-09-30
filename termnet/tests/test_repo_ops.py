"""
Tests for TermNet Repository Operations

Ensures safe git operations and PR management capabilities.
All tests use temporary repositories for complete isolation.
"""

import os
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

from termnet.repo_ops import GitClient, PRClient, RepoOperations, GitResult, PRInfo


class TestGitClient:
    """Test GitClient functionality."""

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize git repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

            # Create initial commit
            test_file = repo_path / "README.md"
            test_file.write_text("# Test Repository\n")
            subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

            yield repo_path

    @pytest.fixture
    def git_client(self, temp_git_repo):
        """Create GitClient instance for testing."""
        return GitClient(str(temp_git_repo))

    def test_git_client_initialization(self, temp_git_repo):
        """Test GitClient initialization and configuration."""
        config = {
            "branch_prefix": "test/",
            "max_commit_size": 500000
        }
        client = GitClient(str(temp_git_repo), config)

        assert client.repo_path == temp_git_repo.resolve()
        assert client.config["branch_prefix"] == "test/"
        assert client.config["max_commit_size"] == 500000
        assert "commit_message_template" in client.config  # Default value

    def test_status_command(self, git_client, temp_git_repo):
        """Test git status functionality."""
        # Clean repo should have empty status
        result = git_client.status()
        assert result.success
        assert len(result.stdout) == 0

        # Add file and check status
        test_file = temp_git_repo / "new_file.txt"
        test_file.write_text("test content")

        result = git_client.status()
        assert result.success
        assert "new_file.txt" in result.stdout

    def test_is_clean(self, git_client, temp_git_repo):
        """Test working tree cleanliness check."""
        # Initially clean
        assert git_client.is_clean()

        # Add untracked file
        test_file = temp_git_repo / "untracked.txt"
        test_file.write_text("untracked content")

        assert not git_client.is_clean()

    def test_get_current_branch(self, git_client):
        """Test current branch detection."""
        branch = git_client.get_current_branch()
        # Fresh repo might be on 'main' or 'master'
        assert branch in ["main", "master"] or branch != "unknown"

    def test_get_current_sha(self, git_client):
        """Test current commit SHA retrieval."""
        sha = git_client.get_current_sha()
        assert len(sha) == 40  # Full SHA length
        assert all(c in "0123456789abcdef" for c in sha.lower())

    def test_add_files(self, git_client, temp_git_repo):
        """Test file staging functionality."""
        # Create test files
        file1 = temp_git_repo / "file1.txt"
        file2 = temp_git_repo / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        # Add files
        result = git_client.add_files(["file1.txt", "file2.txt"])
        assert result.success
        assert "2 files" in result.message

        # Verify files are staged
        status_result = git_client.status()
        assert "file1.txt" in status_result.stdout
        assert "file2.txt" in status_result.stdout

    def test_add_files_empty_list(self, git_client):
        """Test adding empty file list."""
        result = git_client.add_files([])
        assert result.success
        assert "No files to add" in result.message

    def test_add_nonexistent_file(self, git_client):
        """Test adding nonexistent file."""
        result = git_client.add_files(["nonexistent.txt"])
        assert not result.success
        assert "Failed to add files" in result.message

    def test_commit(self, git_client, temp_git_repo):
        """Test commit creation."""
        # Create and stage a file
        test_file = temp_git_repo / "commit_test.txt"
        test_file.write_text("test content for commit")

        # Create commit with files parameter to automatically stage
        result = git_client.commit("Add test file", "This is a test commit", files=["commit_test.txt"])
        assert result.success
        assert "Created commit" in result.message

    def test_commit_with_files_parameter(self, git_client, temp_git_repo):
        """Test commit with automatic file staging."""
        # Create test file but don't stage
        test_file = temp_git_repo / "auto_stage.txt"
        test_file.write_text("auto staged content")

        # Commit with files parameter
        result = git_client.commit(
            "Auto stage and commit",
            "Testing automatic staging",
            files=["auto_stage.txt"]
        )
        assert result.success

    def test_commit_message_formatting(self, git_client, temp_git_repo):
        """Test commit message template formatting."""
        test_file = temp_git_repo / "template_test.txt"
        test_file.write_text("template test")

        result = git_client.commit("Test summary", "Detailed description", files=["template_test.txt"])
        assert result.success

        # Check that commit message follows template
        log_result = git_client._run_git_command(["log", "-1", "--pretty=format:%B"])
        assert "Test summary" in log_result.stdout
        assert "Detailed description" in log_result.stdout
        assert "TermNet" in log_result.stdout

    @patch('subprocess.run')
    def test_git_command_timeout(self, mock_run, git_client):
        """Test git command timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["git", "status"], timeout=30)

        result = git_client.status()
        assert not result.success
        assert "timed out" in result.message
        assert result.return_code == -1

    @patch('subprocess.run')
    def test_git_command_exception(self, mock_run, git_client):
        """Test git command exception handling."""
        mock_run.side_effect = Exception("Mock error")

        result = git_client.status()
        assert not result.success
        assert "failed" in result.message
        assert result.return_code == -1

    def test_reset_to_commit(self, git_client, temp_git_repo):
        """Test repository reset functionality."""
        # Get initial commit SHA
        initial_sha = git_client.get_current_sha()

        # Create another commit
        test_file = temp_git_repo / "reset_test.txt"
        test_file.write_text("content to be reset")
        git_client.commit("Commit to be reset", files=["reset_test.txt"])

        # Reset to initial commit
        result = git_client.reset_to_commit(initial_sha, hard=True)
        assert result.success

        # Verify we're back to initial state
        assert git_client.get_current_sha() == initial_sha
        assert not test_file.exists()


class TestPRClient:
    """Test PRClient functionality with mocked GitHub CLI."""

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            yield repo_path

    @pytest.fixture
    def pr_client(self, temp_git_repo):
        """Create PRClient instance for testing."""
        return PRClient(str(temp_git_repo))

    def test_pr_client_initialization(self, temp_git_repo):
        """Test PRClient initialization."""
        config = {
            "draft_by_default": False,
            "require_reviews": 2
        }
        client = PRClient(str(temp_git_repo), config)

        assert client.repo_path == temp_git_repo.resolve()
        assert client.config["draft_by_default"] is False
        assert client.config["require_reviews"] == 2

    @patch('subprocess.run')
    def test_create_pr_success(self, mock_run, pr_client):
        """Test successful PR creation."""
        # Mock successful gh command
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/user/repo/pull/123"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = pr_client.create_pr("Test PR", "Test description")

        assert result.success
        assert "Created pull request" in result.message
        assert "https://github.com/user/repo/pull/123" in result.stdout

        # Verify gh command was called correctly
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "gh" in args
        assert "pr" in args
        assert "create" in args
        assert "--draft" in args  # Should be draft by default

    @patch('subprocess.run')
    def test_create_pr_with_empty_body(self, mock_run, pr_client):
        """Test PR creation with auto-generated body."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "https://github.com/user/repo/pull/124"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = pr_client.create_pr("Auto body test")

        assert result.success
        # Verify template was used
        call_args = mock_run.call_args[0][0]
        body_index = call_args.index("--body") + 1
        body_content = call_args[body_index]
        assert "## Summary" in body_content
        assert "TermNet" in body_content

    @patch('subprocess.run')
    def test_get_pr_info_success(self, mock_run, pr_client):
        """Test successful PR info retrieval."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"number": 123, "title": "Test PR", "body": "Test body", "state": "OPEN", "headRefOid": "abc123", "baseRefName": "main", "url": "https://github.com/user/repo/pull/123"}'
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        pr_info = pr_client.get_pr_info(123)

        assert pr_info is not None
        assert pr_info.number == 123
        assert pr_info.title == "Test PR"
        assert pr_info.state == "OPEN"
        assert pr_info.head_sha == "abc123"

    @patch('subprocess.run')
    def test_get_pr_info_not_found(self, mock_run, pr_client):
        """Test PR info retrieval for nonexistent PR."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "could not resolve to a PullRequest"
        mock_run.return_value = mock_result

        pr_info = pr_client.get_pr_info(999)
        assert pr_info is None

    @patch('subprocess.run')
    def test_update_pr(self, mock_run, pr_client):
        """Test PR update functionality."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Updated pull request"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = pr_client.update_pr(123, title="New title", body="New body")

        assert result.success
        # Verify correct arguments
        args = mock_run.call_args[0][0]
        assert "pr" in args
        assert "edit" in args
        assert "123" in args
        assert "--title" in args
        assert "New title" in args

    @patch('subprocess.run')
    def test_merge_pr_with_valid_method(self, mock_run, pr_client):
        """Test PR merge with valid method."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Merged pull request"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        result = pr_client.merge_pr(123, merge_method="squash")

        assert result.success
        args = mock_run.call_args[0][0]
        assert "--squash" in args

    def test_merge_pr_with_invalid_method(self, pr_client):
        """Test PR merge with invalid method."""
        result = pr_client.merge_pr(123, merge_method="invalid")

        assert not result.success
        assert "Invalid merge method" in result.message

    @patch('subprocess.run')
    def test_gh_command_timeout(self, mock_run, pr_client):
        """Test GitHub CLI command timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["gh", "pr", "list"], timeout=60)

        result = pr_client.list_prs()
        assert not result.success
        assert "timed out" in result.message


class TestRepoOperations:
    """Test high-level RepoOperations functionality."""

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize git repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

            # Create initial commit
            test_file = repo_path / "README.md"
            test_file.write_text("# Test Repository\n")
            subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

            yield repo_path

    @pytest.fixture
    def repo_ops(self, temp_git_repo):
        """Create RepoOperations instance for testing."""
        return RepoOperations(str(temp_git_repo))

    def test_repo_operations_initialization(self, temp_git_repo):
        """Test RepoOperations initialization."""
        ops = RepoOperations(str(temp_git_repo))

        assert ops.repo_path == temp_git_repo.resolve()
        assert isinstance(ops.git, GitClient)
        assert isinstance(ops.pr, PRClient)

    def test_create_feature_branch(self, repo_ops):
        """Test feature branch creation with automatic naming."""
        result = repo_ops.create_feature_branch("Fix Bug in Authentication System")

        # Should clean up the name
        current_branch = repo_ops.git.get_current_branch()
        assert "fix-bug-in-authentication-system" in current_branch
        assert current_branch.startswith("termnet/")

    def test_commit_changes(self, repo_ops, temp_git_repo):
        """Test committing changes with standardized message."""
        # Create test file
        test_file = temp_git_repo / "feature.py"
        test_file.write_text("# New feature implementation\n")

        result = repo_ops.commit_changes(
            "Add new feature",
            "Implemented user authentication feature",
            files=["feature.py"]
        )

        assert result.success

    @patch.object(PRClient, 'create_pr')
    @patch.object(GitClient, 'push')
    def test_create_pr_for_branch_success(self, mock_push, mock_create_pr, repo_ops):
        """Test atomic PR creation with push."""
        # Mock successful operations
        mock_push.return_value = GitResult(success=True, message="Pushed successfully")
        mock_create_pr.return_value = GitResult(success=True, message="PR created")

        push_result, pr_result = repo_ops.create_pr_for_branch("Test Feature")

        assert push_result.success
        assert pr_result.success
        mock_push.assert_called_once()
        mock_create_pr.assert_called_once()

    @patch.object(PRClient, 'create_pr')
    @patch.object(GitClient, 'push')
    def test_create_pr_for_branch_push_failure(self, mock_push, mock_create_pr, repo_ops):
        """Test PR creation when push fails."""
        # Mock failed push
        mock_push.return_value = GitResult(success=False, message="Push failed")

        push_result, pr_result = repo_ops.create_pr_for_branch("Test Feature")

        assert not push_result.success
        assert not pr_result.success
        assert "Skipped PR creation" in pr_result.message
        mock_create_pr.assert_not_called()

    def test_get_repository_state(self, repo_ops):
        """Test repository state information gathering."""
        state = repo_ops.get_repository_state()

        assert "current_branch" in state
        assert "current_sha" in state
        assert "is_clean" in state
        assert "changed_files" in state
        assert "timestamp" in state

        # Verify data types
        assert isinstance(state["is_clean"], bool)
        assert isinstance(state["changed_files"], list)


class TestGitResult:
    """Test GitResult data structure."""

    def test_git_result_creation(self):
        """Test GitResult creation and attributes."""
        result = GitResult(
            success=True,
            message="Operation completed",
            stdout="output text",
            stderr="",
            return_code=0
        )

        assert result.success is True
        assert result.message == "Operation completed"
        assert result.stdout == "output text"
        assert result.stderr == ""
        assert result.return_code == 0

    def test_git_result_defaults(self):
        """Test GitResult default values."""
        result = GitResult(success=False, message="Failed")

        assert result.success is False
        assert result.message == "Failed"
        assert result.stdout == ""
        assert result.stderr == ""
        assert result.return_code == 0


class TestPRInfo:
    """Test PRInfo data structure."""

    def test_pr_info_creation(self):
        """Test PRInfo creation and attributes."""
        pr_info = PRInfo(
            number=123,
            title="Test PR",
            body="Test description",
            state="OPEN",
            head_sha="abc123def",
            base_branch="main",
            url="https://github.com/user/repo/pull/123"
        )

        assert pr_info.number == 123
        assert pr_info.title == "Test PR"
        assert pr_info.state == "OPEN"
        assert pr_info.head_sha == "abc123def"
        assert pr_info.base_branch == "main"
        assert pr_info.url == "https://github.com/user/repo/pull/123"


class TestRepoOpsIntegration:
    """Integration tests for complete repository operations workflow."""

    @pytest.fixture
    def temp_git_repo(self):
        """Create a temporary git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize git repo
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

            # Create initial commit
            test_file = repo_path / "README.md"
            test_file.write_text("# Test Repository\n")
            subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)

            yield repo_path

    def test_complete_feature_workflow(self, temp_git_repo):
        """Test complete workflow from feature branch to commit."""
        repo_ops = RepoOperations(str(temp_git_repo))

        # 1. Create feature branch
        branch_result = repo_ops.create_feature_branch("add user profile")
        assert branch_result.success

        # 2. Make changes
        feature_file = temp_git_repo / "user_profile.py"
        feature_file.write_text("class UserProfile:\n    pass\n")

        # 3. Commit changes
        commit_result = repo_ops.commit_changes(
            "Add user profile feature",
            "Implemented basic user profile class",
            files=["user_profile.py"]
        )
        assert commit_result.success

        # 4. Verify state
        state = repo_ops.get_repository_state()
        assert "add-user-profile" in state["current_branch"]
        assert state["is_clean"]

    def test_rollback_functionality(self, temp_git_repo):
        """Test rollback to previous commit."""
        repo_ops = RepoOperations(str(temp_git_repo))

        # Get initial state
        initial_sha = repo_ops.git.get_current_sha()

        # Make a commit
        test_file = temp_git_repo / "temp_file.txt"
        test_file.write_text("temporary content")
        commit_result = repo_ops.commit_changes("Temporary commit", files=["temp_file.txt"])
        assert commit_result.success

        # Rollback
        rollback_result = repo_ops.rollback_branch(initial_sha)
        assert rollback_result.success

        # Verify rollback
        assert repo_ops.git.get_current_sha() == initial_sha
        assert not test_file.exists()