"""Tests for DMVL claims engine."""

import unittest


class TestClaimsEngine(unittest.TestCase):
    """Tests for DMVL claim verification."""

    def test_claims_local_smoke(self):
        """Test: run_claims works locally with must_include."""
        from termnet.claims_engine import DMVLClaim, all_ok, run_claims

        res = run_claims(
            [DMVLClaim("echo", "echo hi", must_include="hi")], use_computer=False
        )
        self.assertTrue(all_ok(res))
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].provider, "local")
        self.assertIn("hi", res[0].stdout)

    def test_claims_fail_on_nonzero(self):
        """Test: run_claims detects non-zero exit codes."""
        from termnet.claims_engine import DMVLClaim, all_ok, run_claims

        res = run_claims([DMVLClaim("bad", "bash -c 'exit 3'")])
        self.assertFalse(all_ok(res))
        self.assertEqual(res[0].exit, 3)
        self.assertFalse(res[0].ok)

    def test_claims_fail_on_missing_string(self):
        """Test: run_claims detects missing must_include string."""
        from termnet.claims_engine import DMVLClaim, all_ok, run_claims

        res = run_claims(
            [DMVLClaim("echo", "echo hello", must_include="goodbye")],
            use_computer=False,
        )
        self.assertFalse(all_ok(res))
        self.assertFalse(res[0].ok)


if __name__ == "__main__":
    unittest.main()