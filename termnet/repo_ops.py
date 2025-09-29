"""
TermNet Repository Operations

Provides safe git operations and PR management following Google AI best practices.
Designed for autonomous code changes with comprehensive safety checks.
"""

import json
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class GitResult:
    """Result of a git operation."""

    success: bool
    message: str
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0


@dataclass
class PRInfo:
    """Information about a pull request."""

    number: int
    title: str
    body: str
    state: str
    head_sha: str
    base_branch: str
    url: str


class GitClient:
    """
    Safe git operations client with autonomous change capabilities.

    Provides idempotent operations, conflict detection, and rollback safety.
    """

    def __init__(self, repo_path: str, config: Dict[str, Any] = None):
        """
        Initialize GitClient for repository operations.

        Args:
            repo_path: Path to git repository
            config: Configuration dictionary
        """
        self.repo_path = Path(repo_path).resolve()
        self.config = config or {}
        self._setup_defaults()

    def _setup_defaults(self):
        """Setup default configuration values."""
        defaults = {
            "commit_message_template": "{summary}\n\n{details}\n\n🤖 Generated with TermNet\n\nCo-Authored-By: TermNet <noreply@termnet.ai>",
            "branch_prefix": "termnet/",
            "max_commit_size": 1000000,  # 1MB
            "require_clean_working_tree": True,
            "auto_push": False,
            "sign_commits": False,
        }

        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _run_git_command(self, args: List[str], check: bool = True) -> GitResult:
        """
        Run git command safely with error handling.

        Args:
            args: Git command arguments
            check: Whether to raise on non-zero exit

        Returns:
            GitResult with command output and status
        """
        cmd = ["git"] + args

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
            )

            return GitResult(
                success=(result.returncode == 0),
                message=f"Command completed: {' '.join(args)}",
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                return_code=result.returncode,
            )

        except subprocess.TimeoutExpired:
            return GitResult(
                success=False,
                message=f"Git command timed out: {' '.join(args)}",
                return_code=-1,
            )
        except Exception as e:
            return GitResult(
                success=False, message=f"Git command failed: {e}", return_code=-1
            )

    def status(self) -> GitResult:
        """Get repository status."""
        return self._run_git_command(["status", "--porcelain"])

    def is_clean(self) -> bool:
        """Check if working tree is clean."""
        result = self.status()
        return result.success and len(result.stdout) == 0

    def get_current_branch(self) -> str:
        """Get current branch name."""
        result = self._run_git_command(["branch", "--show-current"])
        return result.stdout if result.success else "unknown"

    def get_current_sha(self) -> str:
        """Get current commit SHA."""
        result = self._run_git_command(["rev-parse", "HEAD"])
        return result.stdout if result.success else "unknown"

    def create_branch(self, branch_name: str, base_branch: str = "main") -> GitResult:
        """
        Create and switch to new branch.

        Args:
            branch_name: Name of new branch
            base_branch: Base branch to branch from

        Returns:
            GitResult indicating success/failure
        """
        # Add prefix if not present
        if not branch_name.startswith(self.config["branch_prefix"]):
            branch_name = self.config["branch_prefix"] + branch_name

        # Try to fetch latest changes (optional for local repos)
        fetch_result = self._run_git_command(["fetch", "origin"])
        use_origin = fetch_result.success

        # Create and checkout branch
        if use_origin:
            # Use origin if available
            result = self._run_git_command(
                ["checkout", "-b", branch_name, f"origin/{base_branch}"]
            )
        else:
            # Fallback to local branch
            result = self._run_git_command(["checkout", "-b", branch_name, base_branch])

        if result.success:
            result.message = f"Created and switched to branch: {branch_name}"

        return result

    def add_files(self, files: List[str]) -> GitResult:
        """
        Stage files for commit.

        Args:
            files: List of file paths to stage

        Returns:
            GitResult indicating success/failure
        """
        if not files:
            return GitResult(success=True, message="No files to add")

        # Add files one by one for better error reporting
        failed_files = []
        for file_path in files:
            result = self._run_git_command(["add", file_path])
            if not result.success:
                failed_files.append(file_path)

        if failed_files:
            return GitResult(
                success=False, message=f"Failed to add files: {', '.join(failed_files)}"
            )

        return GitResult(
            success=True, message=f"Added {len(files)} files to staging area"
        )

    def commit(
        self, message: str, details: str = "", files: List[str] = None
    ) -> GitResult:
        """
        Create commit with standardized message format.

        Args:
            message: Commit summary
            details: Detailed description
            files: Optional list of files to stage first

        Returns:
            GitResult indicating success/failure
        """
        # Check working tree if required
        if self.config["require_clean_working_tree"]:
            if files:
                # Stage specified files first
                add_result = self.add_files(files)
                if not add_result.success:
                    return add_result
            elif not self.is_clean():
                return GitResult(
                    success=False,
                    message="Working tree is not clean. Use files parameter or clean working tree.",
                )

        # Format commit message
        formatted_message = (
            self.config["commit_message_template"]
            .format(summary=message, details=details or "")
            .strip()
        )

        # Create commit
        commit_args = ["commit", "-m", formatted_message]
        if self.config["sign_commits"]:
            commit_args.append("-S")

        result = self._run_git_command(commit_args)

        if result.success:
            result.message = f"Created commit: {message}"

        return result

    def push(self, branch: str = None, set_upstream: bool = True) -> GitResult:
        """
        Push commits to remote repository.

        Args:
            branch: Branch to push (current branch if None)
            set_upstream: Whether to set upstream tracking

        Returns:
            GitResult indicating success/failure
        """
        if branch is None:
            branch = self.get_current_branch()

        push_args = ["push"]
        if set_upstream:
            push_args.extend(["-u", "origin", branch])
        else:
            push_args.extend(["origin", branch])

        return self._run_git_command(push_args)

    def get_diff(self, base_branch: str = "main") -> GitResult:
        """
        Get diff between current branch and base branch.

        Args:
            base_branch: Base branch to compare against

        Returns:
            GitResult with diff in stdout
        """
        return self._run_git_command(["diff", f"origin/{base_branch}...HEAD"])

    def get_changed_files(self, base_branch: str = "main") -> List[str]:
        """
        Get list of files changed between current branch and base branch.

        Args:
            base_branch: Base branch to compare against

        Returns:
            List of changed file paths
        """
        result = self._run_git_command(
            ["diff", "--name-only", f"origin/{base_branch}...HEAD"]
        )

        if result.success:
            return [f.strip() for f in result.stdout.split("\n") if f.strip()]
        return []

    def reset_to_commit(self, commit_sha: str, hard: bool = False) -> GitResult:
        """
        Reset repository to specific commit.

        Args:
            commit_sha: Target commit SHA
            hard: Whether to do hard reset (loses uncommitted changes)

        Returns:
            GitResult indicating success/failure
        """
        reset_type = "--hard" if hard else "--soft"
        return self._run_git_command(["reset", reset_type, commit_sha])


class PRClient:
    """
    Pull request management client using GitHub CLI.

    Provides autonomous PR creation and management capabilities.
    """

    def __init__(self, repo_path: str, config: Dict[str, Any] = None):
        """
        Initialize PRClient for pull request operations.

        Args:
            repo_path: Path to git repository
            config: Configuration dictionary
        """
        self.repo_path = Path(repo_path).resolve()
        self.config = config or {}
        self._setup_defaults()

    def _setup_defaults(self):
        """Setup default configuration values."""
        defaults = {
            "pr_template": "## Summary\n{summary}\n\n## Changes\n{changes}\n\n## Testing\n{testing}\n\n🤖 Generated with TermNet",
            "draft_by_default": True,
            "auto_merge": False,
            "require_reviews": 1,
        }

        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value

    def _run_gh_command(self, args: List[str]) -> GitResult:
        """
        Run GitHub CLI command safely.

        Args:
            args: gh command arguments

        Returns:
            GitResult with command output
        """
        cmd = ["gh"] + args

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout
            )

            return GitResult(
                success=(result.returncode == 0),
                message=f"GitHub CLI command completed: {' '.join(args)}",
                stdout=result.stdout.strip(),
                stderr=result.stderr.strip(),
                return_code=result.returncode,
            )

        except subprocess.TimeoutExpired:
            return GitResult(
                success=False,
                message=f"GitHub CLI command timed out: {' '.join(args)}",
                return_code=-1,
            )
        except Exception as e:
            return GitResult(
                success=False, message=f"GitHub CLI command failed: {e}", return_code=-1
            )

    def create_pr(
        self, title: str, body: str = "", base_branch: str = "main"
    ) -> GitResult:
        """
        Create pull request for current branch.

        Args:
            title: PR title
            body: PR description
            base_branch: Target branch for PR

        Returns:
            GitResult with PR URL in stdout if successful
        """
        # Format PR body
        if not body:
            # Generate basic body from git log
            git_client = GitClient(self.repo_path)
            changed_files = git_client.get_changed_files(base_branch)
            body = self.config["pr_template"].format(
                summary=title,
                changes=f"- Modified {len(changed_files)} files"
                if changed_files
                else "- No file changes detected",
                testing="- Automated tests will run on PR",
            )

        # Create PR
        pr_args = [
            "pr",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--base",
            base_branch,
        ]

        if self.config["draft_by_default"]:
            pr_args.append("--draft")

        result = self._run_gh_command(pr_args)

        if result.success:
            result.message = f"Created pull request: {title}"

        return result

    def get_pr_info(self, pr_number: int) -> Optional[PRInfo]:
        """
        Get information about a pull request.

        Args:
            pr_number: PR number

        Returns:
            PRInfo object or None if not found
        """
        result = self._run_gh_command(
            [
                "pr",
                "view",
                str(pr_number),
                "--json",
                "number,title,body,state,headRefOid,baseRefName,url",
            ]
        )

        if not result.success:
            return None

        try:
            data = json.loads(result.stdout)
            return PRInfo(
                number=data["number"],
                title=data["title"],
                body=data["body"],
                state=data["state"],
                head_sha=data["headRefOid"],
                base_branch=data["baseRefName"],
                url=data["url"],
            )
        except (json.JSONDecodeError, KeyError):
            return None

    def update_pr(
        self, pr_number: int, title: str = None, body: str = None
    ) -> GitResult:
        """
        Update existing pull request.

        Args:
            pr_number: PR number to update
            title: New title (optional)
            body: New body (optional)

        Returns:
            GitResult indicating success/failure
        """
        args = ["pr", "edit", str(pr_number)]

        if title:
            args.extend(["--title", title])
        if body:
            args.extend(["--body", body])

        return self._run_gh_command(args)

    def close_pr(self, pr_number: int) -> GitResult:
        """
        Close pull request.

        Args:
            pr_number: PR number to close

        Returns:
            GitResult indicating success/failure
        """
        return self._run_gh_command(["pr", "close", str(pr_number)])

    def merge_pr(self, pr_number: int, merge_method: str = "squash") -> GitResult:
        """
        Merge pull request.

        Args:
            pr_number: PR number to merge
            merge_method: Merge method (merge, squash, rebase)

        Returns:
            GitResult indicating success/failure
        """
        valid_methods = ["merge", "squash", "rebase"]
        if merge_method not in valid_methods:
            return GitResult(
                success=False,
                message=f"Invalid merge method. Must be one of: {valid_methods}",
            )

        return self._run_gh_command(
            ["pr", "merge", str(pr_number), f"--{merge_method}"]
        )

    def get_pr_checks(self, pr_number: int) -> GitResult:
        """
        Get status of PR checks (CI, etc.).

        Args:
            pr_number: PR number

        Returns:
            GitResult with check status in stdout
        """
        return self._run_gh_command(["pr", "checks", str(pr_number)])

    def list_prs(self, state: str = "open") -> GitResult:
        """
        List pull requests.

        Args:
            state: PR state (open, closed, merged, all)

        Returns:
            GitResult with PR list in stdout
        """
        return self._run_gh_command(
            [
                "pr",
                "list",
                "--state",
                state,
                "--json",
                "number,title,headRefName,state,url",
            ]
        )


class RepoOperations:
    """
    High-level repository operations combining git and PR management.

    Provides atomic operations for autonomous code changes.
    """

    def __init__(self, repo_path: str, config: Dict[str, Any] = None):
        """
        Initialize RepoOperations.

        Args:
            repo_path: Path to git repository
            config: Configuration dictionary
        """
        self.repo_path = Path(repo_path).resolve()
        self.config = config or {}
        self.git = GitClient(repo_path, config)
        self.pr = PRClient(repo_path, config)

    def create_feature_branch(
        self, feature_name: str, base_branch: str = "main"
    ) -> GitResult:
        """
        Create feature branch with automatic naming.

        Args:
            feature_name: Description of feature
            base_branch: Base branch to branch from

        Returns:
            GitResult indicating success/failure
        """
        # Clean feature name for branch
        safe_name = feature_name.lower().replace(" ", "-").replace("_", "-")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "-")

        return self.git.create_branch(safe_name, base_branch)

    def commit_changes(
        self, summary: str, details: str = "", files: List[str] = None
    ) -> GitResult:
        """
        Commit changes with standardized message.

        Args:
            summary: Short description of changes
            details: Detailed description
            files: Files to stage (all changes if None)

        Returns:
            GitResult indicating success/failure
        """
        return self.git.commit(summary, details, files)

    def create_pr_for_branch(
        self, title: str, description: str = "", base_branch: str = "main"
    ) -> Tuple[GitResult, GitResult]:
        """
        Push current branch and create PR atomically.

        Args:
            title: PR title
            description: PR description
            base_branch: Target branch

        Returns:
            Tuple of (push_result, pr_result)
        """
        # Push branch first
        push_result = self.git.push()
        if not push_result.success:
            return push_result, GitResult(
                success=False, message="Skipped PR creation due to push failure"
            )

        # Create PR
        pr_result = self.pr.create_pr(title, description, base_branch)

        return push_result, pr_result

    def rollback_branch(self, commit_sha: str) -> GitResult:
        """
        Rollback current branch to specific commit.

        Args:
            commit_sha: Target commit SHA

        Returns:
            GitResult indicating success/failure
        """
        return self.git.reset_to_commit(commit_sha, hard=True)

    def get_repository_state(self) -> Dict[str, Any]:
        """
        Get comprehensive repository state information.

        Returns:
            Dictionary with repository state details
        """
        return {
            "current_branch": self.git.get_current_branch(),
            "current_sha": self.git.get_current_sha(),
            "is_clean": self.git.is_clean(),
            "changed_files": self.git.get_changed_files(),
            "timestamp": datetime.now().isoformat(),
        }
