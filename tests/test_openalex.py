from academia_mcp.tools import (
    openalex_get_author,
    openalex_get_institution,
    openalex_get_work,
    openalex_search_authors,
    openalex_search_works,
)


def test_openalex_search_works_basic() -> None:
    result = openalex_search_works("attention is all you need")
    assert result.total_count >= 1
    assert result.returned_count >= 1
    assert len(result.results) >= 1
    assert result.offset == 0


def test_openalex_search_works_with_filters() -> None:
    result = openalex_search_works(
        "machine learning",
        limit=5,
        min_cited_by_count=1000,
        publication_year="2020-2023",
    )
    assert result.total_count >= 1
    assert result.returned_count <= 5
    for work in result.results:
        assert work.cited_by_count >= 1000
        if work.publication_year:
            assert 2020 <= work.publication_year <= 2023


def test_openalex_search_works_offset() -> None:
    result = openalex_search_works("transformers", offset=10, limit=5)
    assert result.offset == 10
    assert result.returned_count <= 5


def test_openalex_search_works_sort_by_citations() -> None:
    result = openalex_search_works("neural networks", limit=5, sort_by="cited_by_count")
    assert result.returned_count >= 1
    if len(result.results) > 1:
        assert result.results[0].cited_by_count >= result.results[1].cited_by_count


def test_openalex_get_work_by_doi() -> None:
    work = openalex_get_work("10.65215/pc26a033")
    assert work.title is not None
    assert "attention" in work.title.lower()
    assert len(work.authors) >= 1
    assert work.cited_by_count > 0


def test_openalex_get_work_by_id() -> None:
    work = openalex_get_work("https://openalex.org/W2626778328")
    assert work.title is not None
    assert "attention" in work.title.lower()
    assert work.id is not None
    assert len(work.authors) >= 1


def test_openalex_search_authors_basic() -> None:
    result = openalex_search_authors("Geoffrey Hinton")
    assert result.total_count >= 1
    assert result.returned_count >= 1
    assert len(result.results) >= 1
    assert "hinton" in result.results[0].name.lower()


def test_openalex_search_authors_with_limit() -> None:
    result = openalex_search_authors("John Smith", limit=3)
    assert result.returned_count <= 3


def test_openalex_get_author_by_id() -> None:
    author = openalex_get_author("A2208157607")
    assert author.name is not None
    assert author.works_count > 0
    assert author.cited_by_count > 0


def test_openalex_get_institution_by_id() -> None:
    institution = openalex_get_institution("I136199984")
    assert institution.name is not None
    assert institution.works_count > 0
    assert institution.cited_by_count > 0
