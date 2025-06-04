import pytest

from academia_mcp.tools import anthology_search


def test_anthology_search_basic_search() -> None:
    result = anthology_search('ti:"BERT"')
    assert isinstance(result, str)
    assert len(result) > 0


def test_anthology_search_empty_query() -> None:
    with pytest.raises(AssertionError):
        anthology_search("")


def test_anthology_search_invalid_sort_by() -> None:
    with pytest.raises(AssertionError):
        anthology_search("abs:physics", sort_by="invalid_sort")


def test_anthology_search_invalid_sort_order() -> None:
    with pytest.raises(AssertionError):
        anthology_search("abs:physics", sort_order="invalid_order")


def test_anthology_search_negative_offset() -> None:
    with pytest.raises(AssertionError):
        anthology_search("abs:physics", offset=-1)


def test_anthology_search_negative_limit() -> None:
    with pytest.raises(AssertionError):
        anthology_search("abs:physics", limit=-1)


def test_anthology_search_zero_limit() -> None:
    with pytest.raises(AssertionError):
        anthology_search("abs:physics", limit=0)


def test_anthology_search_offset_limit_combination() -> None:
    result1 = anthology_search("abs:physics", offset=0, limit=5)
    result2 = anthology_search("abs:physics", offset=5, limit=5)
    assert result1 != result2


def test_anthology_search_sort_by_options() -> None:
    valid_sort_options = ["relevance", "published"]
    for sort_option in valid_sort_options:
        result = anthology_search("abs:physics", sort_by=sort_option)
        assert isinstance(result, str)
        assert len(result) > 0


def sort_order_options() -> None:
    result1 = anthology_search("abs:physics", sort_order="ascending")
    result2 = anthology_search("abs:physics", sort_order="descending")
    assert isinstance(result1, str)
    assert len(result1) > 0
    assert isinstance(result2, str)
    assert len(result2) > 0
    assert result1 != result2


def test_anthology_search_unicode_in_query() -> None:
    result = anthology_search('abs:"Schrödinger equation"')
    assert isinstance(result, str)
    assert len(result) > 0


def test_anthology_search_result_format() -> None:
    result = anthology_search("abs:physics")
    assert "title" in result.lower()


def test_anthology_search_type_validation() -> None:
    with pytest.raises(AssertionError):
        anthology_search(123)  # type: ignore
    with pytest.raises(AssertionError):
        anthology_search("abs:physics", offset="0")  # type: ignore
    with pytest.raises(AssertionError):
        anthology_search("abs:physics", limit="5")  # type: ignore
    with pytest.raises(AssertionError):
        anthology_search("abs:physics", sort_by=123)  # type: ignore
    with pytest.raises(AssertionError):
        anthology_search("abs:physics", sort_order=123)  # type: ignore


def test_anthology_search_integration_multiple_pages() -> None:
    first_page = anthology_search("abs:physics", offset=0, limit=5)
    second_page = anthology_search("abs:physics", offset=5, limit=5)
    third_page = anthology_search("abs:physics", offset=10, limit=5)
    assert first_page != second_page != third_page
    assert isinstance(first_page, str)
    assert isinstance(second_page, str)
    assert isinstance(third_page, str)


def test_anthology_search_start_date_only() -> None:
    result = anthology_search('au:wendler AND ti:"Do Llamas work"', start_date="2020-06-01")
    assert "English" in result


def test_anthology_find_conf() -> None:
    result = anthology_search('au:wendler AND ti:"Do Llamas work"')
    assert "2024.acl-long.820" in result
