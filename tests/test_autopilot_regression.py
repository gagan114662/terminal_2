"""
Anti-regression tests for TermNet autopilot.
Locks in the 5/5 test results to prevent regressions.
"""

import os
import subprocess
import sys
import tempfile
import unittest

sys.path.append(".")
from termnet.autopilot import Autopilot  # noqa: E402
from termnet.git_client import GitClient  # noqa: E402


class TestAutopilotRegression(unittest.TestCase):
    """Tests that lock in the 5/5 autopilot behavior."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()

        # Initialize a git repo for testing
        os.chdir(self.test_dir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)

        # Create initial commit
        with open("README.md", "w") as f:
            f.write("# Test Repo\n")
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_clean_repo_only_banner(self):
        """Test: clean repo → only banner message."""
        captured_output = []

        def capture_print(msg):
            captured_output.append(msg)

        autopilot = Autopilot(repo=".", dry_run=True, stdout=capture_print)
        result = autopilot.run("test goal")

        # Should show banner and dry-run message
        self.assertIn("📊 Autopilot status: Ready", captured_output)
        self.assertTrue(
            any("Dry-run: would auto-stash" in msg for msg in captured_output)
        )
        self.assertEqual(result.get("mode"), "dry-run")

    def test_dry_run_dirty_repo_warning_stash_unchanged(self):
        """Test: dry-run dirty → warning present, stash count unchanged."""
        # Make repo dirty
        with open("test_file.txt", "w") as f:
            f.write("test content")

        captured_output = []

        def capture_print(msg):
            captured_output.append(msg)

        git_client = GitClient(".")
        stash_count_before = git_client.stash_count()

        autopilot = Autopilot(repo=".", dry_run=True, stdout=capture_print)
        result = autopilot.run("test goal")

        stash_count_after = git_client.stash_count()

        # Verify output messages
        self.assertIn("📊 Autopilot status: Ready", captured_output)
        self.assertTrue(
            any("Dry-run: would auto-stash" in msg for msg in captured_output)
        )

        # Verify stash count unchanged
        self.assertEqual(stash_count_before, stash_count_after)
        self.assertEqual(result.get("mode"), "dry-run")

    def test_real_run_dirty_stash_pop_messages_count_unchanged(self):
        """Test: real run dirty → stash→pop messages present, count unchanged."""
        # Make repo dirty
        with open("test_file.txt", "w") as f:
            f.write("test content")

        captured_output = []

        def capture_print(msg):
            captured_output.append(msg)

        git_client = GitClient(".")
        stash_count_before = git_client.stash_count()

        autopilot = Autopilot(repo=".", dry_run=False, stdout=capture_print)
        result = autopilot.run("test goal")

        stash_count_after = git_client.stash_count()

        # Verify output messages
        self.assertIn("📊 Autopilot status: Ready", captured_output)
        self.assertTrue(any("Auto-stashing (" in msg for msg in captured_output))
        self.assertTrue(
            any("Restored stashed changes" in msg for msg in captured_output)
        )

        # Verify stash count unchanged (critical!)
        self.assertEqual(stash_count_before, stash_count_after)
        # Check for success or print the error message for debugging
        if result.get("result") != "success":
            print(f"Result: {result}")
        self.assertEqual(result.get("result"), "success")

    def test_pipe_does_not_crash(self):
        """Test: tn status | head -n 1 must not crash."""
        # Test BrokenPipe protection
        try:
            proc = subprocess.Popen(
                ["python3", "-m", "termnet.cli", "status"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.original_cwd,
                env={**os.environ, "PYTHONPATH": self.original_cwd},
            )

            # Read only first line to trigger BrokenPipe
            first_line = proc.stdout.readline()
            proc.stdout.close()
            proc.wait()

            # Should not crash and should contain status message
            self.assertIn(b"Autopilot status: Ready", first_line)

        except Exception as e:
            self.fail(f"Pipe test crashed: {e}")

    def test_completion_flag_created_on_real_run(self):
        """Test: completion flag file is created on real run."""
        # Make repo dirty
        with open("test_file.txt", "w") as f:
            f.write("test content")

        # Ensure logs directory exists
        os.makedirs(".logs", exist_ok=True)

        autopilot = Autopilot(repo=".", dry_run=False, stdout=lambda x: None)
        _ = autopilot.run("test goal")

        # Check that completion flag was created
        flag_file = ".logs/restore_complete.flag"
        self.assertTrue(
            os.path.exists(flag_file), "Completion flag file should be created"
        )

        with open(flag_file, "r") as f:
            flag_content = f.read()

        self.assertIn("Restored stashed changes", flag_content)

    def test_plain_english_entrypoint(self):
        """Test: run_plain_english entrypoint works."""
        captured_output = []

        def capture_print(msg):
            captured_output.append(msg)

        autopilot = Autopilot(repo=".", dry_run=True, stdout=capture_print)
        result = autopilot.run_plain_english("add a test function")

        self.assertTrue(result.get("ok"))
        self.assertEqual(result.get("mode"), "dry-run")
        self.assertEqual(result.get("goal"), "add a test function")


if __name__ == "__main__":
    unittest.main()
