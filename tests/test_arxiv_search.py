import pytest

from academia_mcp.tools import arxiv_search


def test_arxiv_search_basic_search() -> None:
    result = arxiv_search('ti:"PingPong: A Benchmark for Role-Playing Language Models"')
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Ilya Gusev" in result


def test_arxiv_search_empty_query() -> None:
    with pytest.raises(AssertionError):
        arxiv_search("")


def test_arxiv_search_invalid_sort_by() -> None:
    with pytest.raises(AssertionError):
        arxiv_search("abs:physics", sort_by="invalid_sort")


def test_arxiv_search_invalid_sort_order() -> None:
    with pytest.raises(AssertionError):
        arxiv_search("abs:physics", sort_order="invalid_order")


def test_arxiv_search_negative_offset() -> None:
    with pytest.raises(AssertionError):
        arxiv_search("abs:physics", offset=-1)


def test_arxiv_search_negative_limit() -> None:
    with pytest.raises(AssertionError):
        arxiv_search("abs:physics", limit=-1)


def test_arxiv_search_zero_limit() -> None:
    with pytest.raises(AssertionError):
        arxiv_search("abs:physics", limit=0)


def test_arxiv_search_offset_limit_combination() -> None:
    result1 = arxiv_search("abs:physics", offset=0, limit=5)
    result2 = arxiv_search("abs:physics", offset=5, limit=5)
    assert result1 != result2


def test_arxiv_search_sort_by_options() -> None:
    valid_sort_options = ["relevance", "lastUpdatedDate", "submittedDate"]
    for sort_option in valid_sort_options:
        result = arxiv_search("abs:physics", sort_by=sort_option)
        assert isinstance(result, str)
        assert len(result) > 0


def sort_order_options() -> None:
    result1 = arxiv_search("abs:physics", sort_order="ascending")
    result2 = arxiv_search("abs:physics", sort_order="descending")
    assert isinstance(result1, str)
    assert len(result1) > 0
    assert isinstance(result2, str)
    assert len(result2) > 0
    assert result1 != result2


def test_arxiv_search_unicode_in_query() -> None:
    result = arxiv_search('abs:"Schrödinger equation"')
    assert isinstance(result, str)
    assert len(result) > 0


def test_arxiv_search_result_format() -> None:
    result = arxiv_search("abs:physics")
    assert "title" in result.lower()


def test_arxiv_search_type_validation() -> None:
    with pytest.raises(AssertionError):
        arxiv_search(123)  # type: ignore
    with pytest.raises(AssertionError):
        arxiv_search("abs:physics", offset="0")  # type: ignore
    with pytest.raises(AssertionError):
        arxiv_search("abs:physics", limit="5")  # type: ignore
    with pytest.raises(AssertionError):
        arxiv_search("abs:physics", sort_by=123)  # type: ignore
    with pytest.raises(AssertionError):
        arxiv_search("abs:physics", sort_order=123)  # type: ignore


def test_arxiv_search_integration_multiple_pages() -> None:
    first_page = arxiv_search("abs:physics", offset=0, limit=5)
    second_page = arxiv_search("abs:physics", offset=5, limit=5)
    third_page = arxiv_search("abs:physics", offset=10, limit=5)
    assert first_page != second_page != third_page
    assert isinstance(first_page, str)
    assert isinstance(second_page, str)
    assert isinstance(third_page, str)


def test_arxiv_search_date_filter() -> None:
    result = arxiv_search("au:vaswani", start_date="2017-06-01", end_date="2017-07-01", limit=2)
    assert "Attention Is All You Need" in result


def test_arxiv_search_start_date_only() -> None:
    result = arxiv_search('au:vaswani AND ti:"attention is all"', start_date="2017-06-01")
    assert "Attention Is All You Need" in result


def test_arxiv_search_end_date_only() -> None:
    result = arxiv_search('au:vaswani AND ti:"attention is all"', end_date="2017-07-01")
    assert "Attention Is All You Need" in result


def test_arxiv_search_complex_query_vq_vae() -> None:
    result = arxiv_search(
        query='abs:"VQ-VAE" OR abs:"Vector Quantized Variational Autoencoders"',
        limit=1,
        sort_by="submittedDate",
        sort_order="ascending",
        include_abstracts=True,
    )
    assert "1711.00937" in result


def test_arxiv_search_point_e() -> None:
    result = arxiv_search(
        query='ti:"Point-E"',
        limit=1,
        sort_by="submittedDate",
        sort_order="ascending",
        include_abstracts=True,
    )
    assert "2212.08751" in result
