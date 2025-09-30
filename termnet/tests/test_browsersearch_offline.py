from termnet.tools.browsersearch import BrowserSearchTool


def test_browser_search_offline_mode():
    b = BrowserSearchTool()
    assert hasattr(b, "set_offline_mode")
    b.set_offline_mode(True)
    # Test the search method instead of run since it's sync in offline mode
    r = b.search_sync("test")
    assert isinstance(r, list)
    assert len(r) >= 0
