import json

from academia_mcp.tools import s2_citations


def test_s2_citations_pingpong() -> None:
    citations = json.loads(s2_citations("2409.06820"))
    assert citations["total_count"] >= 1
    assert "2502.18308" in str(citations["results"])


def test_s2_citations_transformers() -> None:
    citations = json.loads(s2_citations("1706.03762"))
    assert citations["total_count"] >= 100000
