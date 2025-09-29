"""Tests for Project Mode functionality."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestProjectMode(unittest.TestCase):
    """Tests for project mode CLI and planner."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize a minimal git repo
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cli_help_shows_project_run(self):
        """Test: project run appears in CLI help."""
        result = subprocess.run(
            [self.original_cwd + "/scripts/tn", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertIn("project", result.stdout.lower())

    def test_project_run_writes_yaml(self):
        """Test: project run creates YAML file with brief."""
        result = subprocess.run(
            [self.original_cwd + "/scripts/tn", "project", "run", "demo"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("📦 Project initialized", result.stdout)

        # Check YAML exists
        yaml_path = Path(".termnet/project.yaml")
        self.assertTrue(yaml_path.exists())

        # Check YAML contains brief
        import yaml

        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        self.assertEqual(data["brief"], "demo")

        # Check receipt exists
        receipt_path = Path(".termnet/receipts/receipt_project_init.json")
        self.assertTrue(receipt_path.exists())

        with open(receipt_path, "r") as f:
            receipt = json.load(f)
        self.assertEqual(receipt["brief"], "demo")

    def test_plan_project_shapes_roadmap(self):
        """Test: plan_project returns correct roadmap shape."""
        import sys

        sys.path.insert(0, self.original_cwd)
        from termnet.planner import plan_project

        roadmap = plan_project("test project")

        self.assertEqual(len(roadmap.milestones), 2)
        self.assertEqual(roadmap.milestones[0].name, "Tests First")
        self.assertEqual(roadmap.milestones[1].name, "Implementation")
        self.assertEqual(roadmap.brief, "test project")

    def test_run_gates_smoke(self):
        """Test: run_gates returns dict with flake8 and pytest keys."""
        import sys

        sys.path.insert(0, self.original_cwd)
        from termnet.gates import run_gates

        res = run_gates()
        self.assertIn("flake8", res)
        self.assertIn("pytest", res)
        self.assertIsInstance(res["flake8"], int)
        self.assertIsInstance(res["pytest"], int)

    def test_project_run_real_writes_receipts(self):
        """Test: project run -R writes start and repo-status receipts."""
        result = subprocess.run(
            [self.original_cwd + "/scripts/tn", "project", "run", "-R", "test brief"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("✅ Project kickoff receipts written", result.stdout)

        # Check for timestamped receipts
        receipts_dir = Path(".termnet/receipts")
        self.assertTrue(receipts_dir.exists())

        receipt_files = list(receipts_dir.glob("receipt_*_start.json"))
        self.assertGreater(len(receipt_files), 0, "Start receipt should exist")

        task_receipt_files = list(receipts_dir.glob("receipt_*_task_repo-status.json"))
        self.assertGreater(
            len(task_receipt_files), 0, "Repo-status task receipt should exist"
        )

        # Verify start receipt contains brief and args
        start_receipt = json.loads(receipt_files[0].read_text())
        self.assertEqual(start_receipt["brief"], "test brief")
        self.assertIn("args", start_receipt)

        # Verify repo-status receipt has expected keys
        task_receipt = json.loads(task_receipt_files[0].read_text())
        self.assertIn("name", task_receipt)
        self.assertIn("cmd", task_receipt)
        self.assertIn("exit", task_receipt)
        self.assertIn("provider", task_receipt)

    def test_acceptance_scaffold_created(self):
        """Test: acceptance scaffold is created by project run."""
        result = subprocess.run(
            [self.original_cwd + "/scripts/tn", "project", "run", "test brief"],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("✅ Acceptance scaffold:", result.stdout)

        # Check scaffold files exist
        acceptance_dir = Path("tests/acceptance")
        self.assertTrue(acceptance_dir.exists())

        init_file = acceptance_dir / "__init__.py"
        self.assertTrue(init_file.exists())

        test_file = acceptance_dir / "test_acceptance_smoke.py"
        self.assertTrue(test_file.exists())

        # Verify test file has skipped test
        test_content = test_file.read_text()
        self.assertIn("@unittest.skip", test_content)
        self.assertIn("test_acceptance_placeholder", test_content)


if __name__ == "__main__":
    unittest.main()
