import json

from academia_mcp.tools import web_search


def test_web_search_base() -> None:
    result = web_search("autoregressive models path-star graphs", limit=20)
    results = json.loads(result)
    assert results
    assert "score" not in str(results)


def test_web_search_exa() -> None:
    result = web_search("autoregressive models path-star graphs", provider="exa", limit=10)
    assert result
    results = json.loads(result)
    assert results


def test_web_search_brave() -> None:
    result = web_search("autoregressive models path-star graphs", provider="brave", limit=10)
    assert "The Mystery of the Pathological" in result
    results = json.loads(result)
    assert results


def test_web_search_bug() -> None:
    results = web_search(
        '"Can Hiccup Supply Enough Fish to Maintain a Dragon\'s Diet?" University of Leicester'
    )
    assert results
    assert len(results.splitlines()) == 1


def test_web_search_include_domains() -> None:
    results = web_search(
        "autoregressive models path-star graphs",
        include_domains=["wikipedia.org"],
    )
    assert results
    results = json.loads(results)
    assert results
    assert len(results["results"]) > 0
    assert all("wikipedia.org" in result["url"] for result in results["results"])


def test_web_search_include_query_domains() -> None:
    results = web_search(
        "site:wikipedia.org autoregressive models path-star graphs",
    )
    assert results
    results = json.loads(results)
    assert results
    assert len(results["results"]) > 0
    assert all("wikipedia.org" in result["url"] for result in results["results"])
