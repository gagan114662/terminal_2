#!/usr/bin/env python3
"""
Autonomous task runner for TermNet.
Polls GitHub issues labeled 'auto' and processes them autonomously.
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import requests


class AutoTaskRunner:
    """Autonomous runner that processes GitHub issues labeled 'auto'."""

    def __init__(
        self,
        repo_owner: str,
        repo_name: str,
        github_token: str = None,
        poll_interval: int = 300,
        max_tasks_per_run: int = 3,
    ):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.poll_interval = poll_interval  # seconds
        self.max_tasks_per_run = max_tasks_per_run

        if not self.github_token:
            raise ValueError("GitHub token required (GITHUB_TOKEN env var or --token)")

        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

        # State tracking
        self.processed_issues = set()
        self.last_poll_time = datetime.now()

        # Setup logging
        self.log_file = Path(".termnet/auto_runner.log")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} [{level}] {message}"

        print(log_entry)

        try:
            with open(self.log_file, "a") as f:
                f.write(log_entry + "\n")
        except Exception:
            pass  # Don't fail on logging errors

    def get_auto_issues(self) -> List[Dict]:
        """Get open issues labeled 'auto'."""
        try:
            url = f"{self.base_url}/issues"
            params = {
                "labels": "auto",
                "state": "open",
                "sort": "created",
                "direction": "asc",
            }

            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()

            issues = response.json()
            self.log(f"Found {len(issues)} open issues with 'auto' label")

            return issues

        except Exception as e:
            self.log(f"Failed to fetch issues: {e}", "ERROR")
            return []

    def process_issue(self, issue: Dict) -> bool:
        """Process a single GitHub issue."""
        issue_number = issue["number"]
        issue_title = issue["title"]
        issue_body = issue.get("body", "")

        self.log(f"Processing issue #{issue_number}: {issue_title}")

        try:
            # Create feature branch
            branch_name = f"auto/issue-{issue_number}"
            self.log(f"Creating branch: {branch_name}")

            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                check=True,
                capture_output=True,
            )

            # Extract task from issue
            task_text = self._extract_task_from_issue(issue_title, issue_body)
            self.log(f"Extracted task: {task_text}")

            # Run autopilot
            result = self._run_autopilot_task(task_text)

            if not result["success"]:
                self.log(f"Autopilot failed: {result['error']}", "ERROR")
                self._cleanup_branch(branch_name)
                return False

            # Create PR if changes were made
            if self._has_changes():
                pr_result = self._create_pull_request(issue, branch_name, task_text)

                if pr_result["success"]:
                    # Comment on issue with PR link
                    self._comment_on_issue(
                        issue_number,
                        f"🤖 Auto-processed in PR #{pr_result['pr_number']}",
                    )

                    # Close issue as completed
                    self._close_issue(issue_number, "completed")

                    self.log(
                        f"Successfully created PR #{pr_result['pr_number']} for issue #{issue_number}"
                    )
                    return True
                else:
                    self.log(f"Failed to create PR: {pr_result['error']}", "ERROR")
                    self._cleanup_branch(branch_name)
                    return False
            else:
                self.log(f"No changes made for issue #{issue_number}")
                self._cleanup_branch(branch_name)
                self._comment_on_issue(
                    issue_number, "🤖 Auto-processed but no changes were needed"
                )
                self._close_issue(issue_number, "not planned")
                return True

        except Exception as e:
            self.log(f"Failed to process issue #{issue_number}: {e}", "ERROR")
            self._cleanup_branch(f"auto/issue-{issue_number}")
            return False

    def _extract_task_from_issue(self, title: str, body: str) -> str:
        """Extract actionable task from GitHub issue."""
        # Look for task markers in body
        if "TASK:" in body.upper():
            for line in body.split("\n"):
                if line.upper().strip().startswith("TASK:"):
                    return line.split(":", 1)[1].strip()

        # Fallback to title
        return title

    def _run_autopilot_task(self, task_text: str) -> Dict:
        """Run autopilot with the given task."""
        try:
            # Use PYTHONPATH=. python3 -m termnet.cli say
            env = os.environ.copy()
            env["PYTHONPATH"] = "."

            cmd = [sys.executable, "-m", "termnet.cli", "say", task_text]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                env=env,
                timeout=300,
            )  # 5 minute timeout

            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            else:
                return {"success": False, "error": result.stderr}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Task timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _has_changes(self) -> bool:
        """Check if there are uncommitted changes."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"], capture_output=True, text=True
            )
            return len(result.stdout.strip()) > 0
        except Exception:
            return False

    def _create_pull_request(
        self, issue: Dict, branch_name: str, task_text: str
    ) -> Dict:
        """Create PR for the changes."""
        try:
            # Commit changes
            subprocess.run(["git", "add", "."], check=True)

            commit_msg = (
                f"feat: {task_text}\n\nAuto-generated from issue #{issue['number']}"
            )
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)

            # Push branch
            subprocess.run(["git", "push", "origin", branch_name], check=True)

            # Create PR via API
            pr_data = {
                "title": f"Auto: {task_text}",
                "head": branch_name,
                "base": "main",
                "body": (
                    f"🤖 **Auto-generated PR**\n\n"
                    f"Resolves #{issue['number']}\n\n"
                    f"Task: {task_text}"
                ),
            }

            url = f"{self.base_url}/pulls"
            response = requests.post(url, headers=self.headers, json=pr_data)
            response.raise_for_status()

            pr = response.json()
            return {
                "success": True,
                "pr_number": pr["number"],
                "pr_url": pr["html_url"],
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _comment_on_issue(self, issue_number: int, comment: str):
        """Add comment to GitHub issue."""
        try:
            url = f"{self.base_url}/issues/{issue_number}/comments"
            data = {"body": comment}
            requests.post(url, headers=self.headers, json=data)
        except Exception as e:
            self.log(f"Failed to comment on issue #{issue_number}: {e}", "ERROR")

    def _close_issue(self, issue_number: int, reason: str = "completed"):
        """Close GitHub issue."""
        try:
            url = f"{self.base_url}/issues/{issue_number}"
            data = {"state": "closed", "state_reason": reason}
            requests.patch(url, headers=self.headers, json=data)
        except Exception as e:
            self.log(f"Failed to close issue #{issue_number}: {e}", "ERROR")

    def _cleanup_branch(self, branch_name: str):
        """Clean up feature branch."""
        try:
            subprocess.run(["git", "checkout", "main"], capture_output=True)
            subprocess.run(["git", "branch", "-D", branch_name], capture_output=True)
        except Exception as e:
            self.log(f"Failed to cleanup branch {branch_name}: {e}", "ERROR")

    def run_once(self) -> Dict:
        """Run one polling cycle."""
        self.log("Starting polling cycle")

        # Ensure we're on main branch
        try:
            subprocess.run(["git", "checkout", "main"], check=True, capture_output=True)
            subprocess.run(
                ["git", "pull", "origin", "main"], check=True, capture_output=True
            )
        except Exception as e:
            self.log(f"Failed to update main branch: {e}", "ERROR")
            return {"success": False, "error": "Failed to update main branch"}

        # Get auto issues
        issues = self.get_auto_issues()

        if not issues:
            self.log("No auto issues to process")
            return {"success": True, "processed": 0}

        # Process issues (up to max_tasks_per_run)
        processed = 0
        for issue in issues[: self.max_tasks_per_run]:
            issue_number = issue["number"]

            # Skip if already processed in this session
            if issue_number in self.processed_issues:
                continue

            success = self.process_issue(issue)
            self.processed_issues.add(issue_number)

            if success:
                processed += 1

            # Brief pause between issues
            time.sleep(10)

        self.log(f"Processed {processed} issues")
        return {"success": True, "processed": processed}

    def run_daemon(self):
        """Run as daemon with continuous polling."""
        self.log(
            f"Starting autonomous task runner daemon (poll interval: {self.poll_interval}s)"
        )

        try:
            while True:
                cycle_result = self.run_once()

                if not cycle_result["success"]:
                    self.log(
                        f"Cycle failed: {cycle_result.get('error', 'Unknown error')}",
                        "ERROR",
                    )

                # Wait for next cycle
                self.log(f"Waiting {self.poll_interval} seconds until next cycle")
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            self.log("Daemon stopped by user")
        except Exception as e:
            self.log(f"Daemon crashed: {e}", "ERROR")
            raise


def main():
    """CLI interface for auto task runner."""
    import argparse

    parser = argparse.ArgumentParser(description="TermNet Autonomous Task Runner")
    parser.add_argument("--owner", required=True, help="GitHub repo owner")
    parser.add_argument("--repo", required=True, help="GitHub repo name")
    parser.add_argument("--token", help="GitHub token (or use GITHUB_TOKEN env var)")
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Poll interval in seconds (default: 300)",
    )
    parser.add_argument(
        "--max-tasks", type=int, default=3, help="Max tasks per cycle (default: 3)"
    )
    parser.add_argument(
        "--once", action="store_true", help="Run once instead of daemon mode"
    )

    args = parser.parse_args()

    try:
        runner = AutoTaskRunner(
            repo_owner=args.owner,
            repo_name=args.repo,
            github_token=args.token,
            poll_interval=args.interval,
            max_tasks_per_run=args.max_tasks,
        )

        if args.once:
            result = runner.run_once()
            if result["success"]:
                print(f"✅ Successfully processed {result['processed']} issues")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        else:
            runner.run_daemon()

    except Exception as e:
        print(f"❌ Runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
