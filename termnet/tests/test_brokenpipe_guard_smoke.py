"""
Smoke test for BrokenPipe guard in autopilot output.
Ensures piping to head doesn't crash.
"""

import subprocess
import sys
import unittest


class TestBrokenPipeGuard(unittest.TestCase):
    """Test that piping autopilot output doesn't crash on BrokenPipe."""

    def test_pipe_to_head_no_crash(self):
        """Test: ./scripts/tn status | head -n 1 doesn't crash."""
        # Run: ./scripts/tn status | head -n 1
        tn_proc = subprocess.Popen(
            ["./scripts/tn", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        head_proc = subprocess.Popen(
            ["head", "-n", "1"],
            stdin=tn_proc.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Allow tn_proc to receive SIGPIPE when head closes
        tn_proc.stdout.close()

        stdout, stderr = head_proc.communicate()
        tn_proc.wait()

        # Assert head got output and tn didn't crash
        self.assertIn("📊 Autopilot status: Ready", stdout)
        # tn may exit with SIGPIPE (141) or clean exit (0), both acceptable
        self.assertIn(tn_proc.returncode, [0, 141, -13])  # 0=clean, 141=SIGPIPE, -13=SIGPIPE on some systems


if __name__ == "__main__":
    unittest.main()