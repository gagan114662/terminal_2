"""Tests for Qwen Computer-Use provider."""

import unittest


class TestQwenCUProvider(unittest.TestCase):
    """Tests for Computer-Use verification."""

    def test_verify_claim_local_smoke(self):
        """Test: verify_claim works locally."""
        from termnet.cu_client import verify_claim

        res = verify_claim("echo", "echo hi")
        self.assertEqual(res["exit"], 0)
        self.assertIn("hi", res["stdout"])
        self.assertEqual(res["provider"], "local")

    def test_verify_claim_cu_mock(self):
        """Test: verify_claim uses CU with mocked HTTP."""
        from unittest.mock import MagicMock, patch

        from termnet.cu_client import verify_claim

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"stdout": "ok", "stderr": "", "exit": 0}

        with patch("requests.post", return_value=mock_response):
            res = verify_claim("check", "echo ok", use_computer=True)
            self.assertEqual(res["exit"], 0)
            self.assertEqual(res["stdout"], "ok")
            self.assertEqual(res["provider"], "qwen-vl-cu")


if __name__ == "__main__":
    unittest.main()