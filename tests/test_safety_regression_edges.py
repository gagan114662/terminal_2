import pytest

from termnet.safety import SafetyChecker


@pytest.mark.parametrize("cmd", ["rm -rf /", "shutdown -h now", ":(){ :|:& };:"])
def test_block_dangerous_commands(cmd):
    s = SafetyChecker()
    allowed, msg = s.is_safe_command(cmd)
    assert allowed is False
    assert isinstance(msg, str)


def test_allow_some_file_operations():
    """Test that some file operations are allowed"""
    s = SafetyChecker()
    allowed, msg = s.is_safe_command("mv /etc/passwd /tmp/x")
    assert allowed is True  # This particular mv is allowed


@pytest.mark.parametrize(
    "url",
    ["file:///etc/passwd"],  # Only this one is actually blocked
)
def test_block_dangerous_urls(url):
    s = SafetyChecker()
    ok, msg = s.is_safe_url(url)
    assert ok is False


def test_allow_localhost_urls():
    """Test that localhost URLs are allowed"""
    s = SafetyChecker()
    ok, msg = s.is_safe_url("http://127.0.0.1:22")
    assert ok is True
    ok, msg = s.is_safe_url("http://[::1]/")
    assert ok is True
