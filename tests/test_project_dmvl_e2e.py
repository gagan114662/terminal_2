"""End-to-end tests for DMVL project mode."""

import subprocess
import unittest


class TestProjectDMVLE2E(unittest.TestCase):
    """End-to-end acceptance tests for DMVL project mode."""

    def test_project_dmvl_e2e_smoke(self):
        """Test: project run returns 0 in dry-run mode."""
        result = subprocess.run(
            "./scripts/tn project run 'demo e2e' --dry-run",
            shell=True,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("📦 Project initialized", result.stdout)


if __name__ == "__main__":
    unittest.main()
