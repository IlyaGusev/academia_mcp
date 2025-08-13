from academia_mcp.tools import web_search


def test_web_search() -> None:
    result = web_search("autoregressive models path-star graphs", provider="tavily")
    assert "The Mystery of the Pathological" in result
    assert "The Pitfalls of Next-Token Prediction" in result


def test_web_search_exa() -> None:
    result = web_search("autoregressive models path-star graphs", provider="exa")
    assert result
