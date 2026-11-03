import importlib
from typing import Any, Dict, List

import pytest

from academia_mcp.settings import settings
from academia_mcp.tools import keenable_web_search, web_search

web_search_module = importlib.import_module("academia_mcp.tools.web_search")


class _FakeResponse:
    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    def json(self) -> Dict[str, Any]:
        return self._data


def test_keenable_web_search_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: List[Dict[str, Any]] = []

    def fake_post(url: str, payload: Dict[str, Any], api_key: str, **kwargs: Any) -> _FakeResponse:
        calls.append({"url": url, "payload": payload, "api_key": api_key, **kwargs})
        return _FakeResponse(
            {
                "results": [
                    {"title": "A", "url": "https://a.example/", "description": "d", "snippet": "s"},
                    {
                        "title": "B",
                        "url": "https://b.example/",
                        "description": "",
                        "snippet": "x" * 900,
                    },
                    {"title": "no url"},
                ]
            }
        )

    for key in ("TAVILY_API_KEY", "EXA_API_KEY", "BRAVE_API_KEY"):
        monkeypatch.setattr(settings, key, None)
    monkeypatch.setattr(settings, "KEENABLE_API_KEY", "kn-test")
    monkeypatch.setattr(web_search_module, "post_with_retries", fake_post)

    result = keenable_web_search("query", limit=5)
    assert result.search_provider == "keenable"
    assert [(e.id, e.content) for e in result.results] == [
        ("https://a.example/", "d"),
        ("https://b.example/", "x" * 500),
    ]
    assert calls[0]["url"] == "https://api.keenable.ai/v1/search"
    assert calls[0]["payload"] == {"query": "query", "max_results": 5}
    assert calls[0]["extra_headers"]["X-API-Key"] == "kn-test"
    assert calls[0]["extra_headers"]["X-Keenable-Title"] == "Academia MCP"

    # Default provider (tavily) is unavailable, so web_search falls through to keenable.
    assert web_search("query", limit=5).search_provider == "keenable"
