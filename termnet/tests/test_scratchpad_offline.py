from termnet.tools.scratchpad import ScratchpadTool


def test_scratchpad_offline_mode_write_read_clear():
    t = ScratchpadTool()
    assert hasattr(t, "set_offline_mode")
    t.set_offline_mode(True)

    r1 = t.write("test_key", "hello")
    assert isinstance(r1, str)
    assert "test_key" in r1

    r2 = t.read("test_key")
    assert "hello" in r2

    r3 = t.clear()
    assert isinstance(r3, dict)
