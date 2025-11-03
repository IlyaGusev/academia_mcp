from academia_mcp.tools import (
    s2_get_citations,
    s2_get_references,
    s2_get_info,
    s2_search,
)


def test_s2_citations_pingpong() -> None:
    citations = s2_get_citations("2409.06820")
    assert citations.total_count >= 1
    assert "2502.18308" in str(citations.results)


def test_s2_citations_transformers() -> None:
    citations = s2_get_citations("1706.03762")
    assert citations.total_count >= 100000


def test_s2_citations_reversed() -> None:
    citations = s2_get_references("1706.03762")
    assert citations.total_count <= 100


def test_s2_citations_versions() -> None:
    citations = s2_get_citations("2409.06820v4")
    assert citations.total_count >= 1


def test_s2_get_info() -> None:
    info = s2_get_info("2409.06820")
    assert info.title is not None
    assert info.authors is not None
    assert info.external_ids is not None
    assert info.venue is not None
    assert info.citation_count is not None
    assert info.publication_date is not None
    assert info.external_ids["CorpusId"] == 272593138


def test_s2_search_base() -> None:
    result = s2_search("transformers")
    assert result.total_count >= 1
    assert "transformers" in str(result.results).lower()
    assert result.offset == 0
    assert result.returned_count == 5


def test_s2_search_offset() -> None:
    result = s2_search("transformers", offset=10)
    assert result.total_count >= 1
    assert "transformers" in str(result.results).lower()
    assert result.offset == 10
    assert result.returned_count == 5


def test_s2_search_min_citation_count() -> None:
    result = s2_search("transformers", min_citation_count=100000)
    assert result.total_count >= 2 and result.total_count <= 10


def test_s2_search_publication_date() -> None:
    result = s2_search(
        "transformers", min_citation_count=100000, publication_date="2017-01-01:2017-12-31"
    )
    assert result.total_count == 1
