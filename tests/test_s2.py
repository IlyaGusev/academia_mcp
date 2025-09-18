import json

from academia_mcp.tools import (
    s2_get_citations,
    s2_get_references,
    s2_corpus_id_from_arxiv_id,
    s2_get_info,
)


def test_s2_citations_pingpong() -> None:
    citations = json.loads(s2_get_citations("2409.06820"))
    assert citations["total_count"] >= 1
    assert "2502.18308" in str(citations["results"])


def test_s2_citations_transformers() -> None:
    citations = json.loads(s2_get_citations("1706.03762"))
    assert citations["total_count"] >= 100000


def test_s2_citations_reversed() -> None:
    citations = json.loads(s2_get_references("1706.03762"))
    assert citations["total_count"] <= 100


def test_s2_citations_versions() -> None:
    citations = json.loads(s2_get_citations("2409.06820v4"))
    assert citations["total_count"] >= 1


def test_s2_corpus_id_from_arxiv_id() -> None:
    assert s2_corpus_id_from_arxiv_id("2409.06820") == 272593138


def test_s2_get_info() -> None:
    info = json.loads(s2_get_info("2409.06820"))
    assert info["title"] is not None
    assert info["authors"] is not None
    assert info["externalIds"] is not None
    assert info["venue"] is not None
    assert info["citationCount"] is not None
    assert info["publicationDate"] is not None
    assert info["externalIds"]["CorpusId"] == 272593138
