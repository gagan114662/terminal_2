from termnet.tools.terminal import TerminalTool


def test_terminal_contract_offline_echo():
    t = TerminalTool()
    t.set_offline_mode(True)
    out = t.run("echo hello")
    assert set(out.keys()) >= {"stdout", "stderr", "exit_code"}
    assert out["exit_code"] in (0, 124)
