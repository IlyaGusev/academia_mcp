from academia_mcp.tools import web_search


def test_web_search_base() -> None:
    result = web_search("autoregressive models path-star graphs", limit=20)
    assert result.results


def test_web_search_exa() -> None:
    result = web_search("autoregressive models path-star graphs", provider="exa", limit=10)
    assert result.results
    assert result.search_provider == "exa"
    for entry in result.results:
        assert entry.content is not None


def test_web_search_tavily() -> None:
    result = web_search("autoregressive models path-star graphs", provider="tavily", limit=10)
    assert result.results
    assert result.search_provider == "tavily"
    for entry in result.results:
        assert entry.content is not None


def test_web_search_brave() -> None:
    result = web_search("autoregressive models path-star graphs", provider="brave", limit=10)
    assert "The Mystery of the Pathological" in str(result)
    assert result.search_provider == "brave"
    assert result.results
    for entry in result.results:
        assert entry.content is not None


def test_web_search_bug() -> None:
    results = web_search(
        '"Can Hiccup Supply Enough Fish to Maintain a Dragon\'s Diet?" University of Leicester'
    )
    assert results.results
    assert len(results.model_dump_json().splitlines()) == 1


def test_web_search_include_domains() -> None:
    results = web_search(
        "autoregressive models path-star graphs",
        include_domains=["wikipedia.org"],
    )
    assert results
    assert results.results
    assert len(results.results) > 0
    assert all("wikipedia.org" in result.id for result in results.results)


def test_web_search_include_query_domains() -> None:
    results = web_search(
        "site:wikipedia.org autoregressive models path-star graphs",
    )
    assert results.results
    assert all("wikipedia.org" in result.id for result in results.results)
