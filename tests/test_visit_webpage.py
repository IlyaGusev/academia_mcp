from academia_mcp.tools import visit_webpage


def test_visit_webpage_basic() -> None:
    content = visit_webpage("https://example.com/")
    assert content is not None
    assert "Example Domain" in content
    assert "illustrative" in content


def test_visit_webpage_exa() -> None:
    content = visit_webpage("https://example.com/", provider="exa")
    assert content is not None
    assert "Example Domain" in content
    assert "illustrative" in content
