# Based on
# https://github.com/jonatasgrosman/findpapers/blob/master/findpapers/searchers/arxiv_searcher.py
# https://info.arxiv.org/help/api/user-manual.html

import json
import re
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date

import xmltodict

from academia_mcp.utils import get_with_retries

BASE_URL = "http://export.arxiv.org"
URL_TEMPLATE = "{base_url}/api/query?search_query={query}&start={start}&sortBy={sort_by}&sortOrder={sort_order}&max_results={limit}"
SORT_BY_OPTIONS = ("relevance", "lastUpdatedDate", "submittedDate")
SORT_ORDER_OPTIONS = ("ascending", "descending")


def _format_text_field(text: str) -> str:
    return " ".join([line.strip() for line in text.split() if line.strip()])


def _format_authors(authors: Union[List[Dict[str, str]], Dict[str, str]]) -> str:
    if not authors:
        return ""
    if isinstance(authors, dict):
        authors = [authors]
    names = [author["name"] for author in authors]
    result = ", ".join(names[:3])
    if len(names) > 3:
        result += f", and {len(names) - 3} more authors"
    return result


def _format_categories(categories: Union[List[Dict[str, Any]], Dict[str, Any]]) -> str:
    if not categories:
        return ""
    if isinstance(categories, dict):
        categories = [categories]
    clean_categories = [c.get("@term", "") for c in categories]
    clean_categories = [c.strip() for c in clean_categories if c.strip()]
    return ", ".join(clean_categories)


def _format_date(date: str) -> str:
    dt = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%B %d, %Y")


def _clean_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": entry["id"].split("/")[-1],
        "title": _format_text_field(entry["title"]),
        "authors": _format_authors(entry["author"]),
        "abstract": _format_text_field(entry["summary"]),
        "published": _format_date(entry["published"]),
        "updated": _format_date(entry["updated"]),
        "categories": _format_categories(entry.get("category", {})),
        "comment": _format_text_field(entry.get("arxiv:comment", {}).get("#text", "")),
    }


def _convert_to_yyyymmddtttt(date_str: str) -> str:
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y%m%d") + "0000"
    except ValueError as e:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD format.") from e


def _has_cyrillic(text: str) -> bool:
    return bool(re.search("[а-яА-Я]", text))


def _compose_query(
    orig_query: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> str:
    query: str = orig_query.replace(" AND NOT ", " ANDNOT ")
    if "-" in query:
        query = f"({query}) OR ({query.replace('-', ' ')})"

    if start_date or end_date:
        if not start_date:
            start_date = "1900-01-01"
        if not end_date:
            today = date.today()
            end_date = today.strftime("%Y-%m-%d")
        date_filter = (
            f"[{_convert_to_yyyymmddtttt(start_date)} TO {_convert_to_yyyymmddtttt(end_date)}]"
        )
        query = f"({query}) AND submittedDate:{date_filter}"

    query = query.replace(" ", "+")
    query = query.replace('"', "%22")
    query = query.replace("(", "%28")
    query = query.replace(")", "%29")
    return query


def _format_entries(
    entries: List[Dict[str, Any]],
    start_index: int,
    include_abstracts: bool,
    total_results: int,
) -> str:
    clean_entries: List[Dict[str, Any]] = []
    for entry_num, entry in enumerate(entries):
        clean_entry = _clean_entry(entry)
        if not include_abstracts:
            clean_entry.pop("abstract")
        clean_entry["index"] = start_index + entry_num
        clean_entries.append(clean_entry)
    return json.dumps(
        {
            "total_count": total_results,
            "returned_count": len(entries),
            "offset": start_index,
            "results": clean_entries,
        },
        ensure_ascii=False,
    )


def arxiv_search(
    query: str,
    offset: Optional[int] = 0,
    limit: Optional[int] = 5,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    sort_by: Optional[str] = "relevance",
    sort_order: Optional[str] = "descending",
    include_abstracts: Optional[bool] = False,
) -> str:
    """
    Search arXiv papers with field-specific queries.

    Fields:
        all: (all fields), ti: (title), au: (author),
        abs: (abstract), cat: (category), id: (ID without version)

    Operators:
        AND, OR, ANDNOT

    Please always specify the fields. Search should always be field-specific.
    You can search for an exact match of an entire phrase by enclosing the phrase in double quotes.
    If you do not need an exact match of a phrase, use single terms with OR/AND.
    Boolean operators are strict. OR is better in most cases.
    Do not include date constraints in the query: use "start_date" and "end_date" parameters instead.
    Use Latin script for names. For example, search "Ilya Gusev" instead of "Илья Гусев".

    Example queries:
        all:"machine learning"
        au:"del maestro"
        au:vaswani AND abs:"attention is all"
        all:role OR all:playing OR all:"language model"
        (au:vaswani OR au:"del maestro") ANDNOT ti:attention

    Returns a JSON object serialized to a string. The structure is:
    {"total_count": ..., "returned_count": ..., "offset": ..., "results": [...]}
    Every item in the "results" has the following fields:
    ("index", "id", "title", "authors", "abstract", "published", "updated", "categories", "comment")
    Use `json.loads` to deserialize the result if you want to get specific fields.

    Args:
        query: The search query, required.
        offset: The offset to scroll search results. 10 items will be skipped if offset=10. 0 by default.
        limit: The maximum number of items to return. limit=5 by default, limit=10 is the maximum.
        start_date: Start date in %Y-%m-%d format. None by default.
        end_date: End date in %Y-%m-%d format. None by default.
        sort_by: 3 options to sort by: relevance, lastUpdatedDate, submittedDate. relevance by default.
        sort_order: 2 sort orders: ascending, descending. descending by default.
        include_abstracts: include abstracts in the result or not. False by default.
    """

    assert isinstance(query, str), "Error: Your search query must be a string"
    assert isinstance(offset, int), "Error: offset should be an integer"
    assert isinstance(limit, int), "Error: limit should be an integer"
    assert isinstance(sort_by, str), "Error: sort_by should be a string"
    assert isinstance(sort_order, str), "Error: sort_order should be a string"
    assert query.strip(), "Error: Your query should not be empty"
    assert sort_by in SORT_BY_OPTIONS, f"Error: sort_by should be one of {SORT_BY_OPTIONS}"
    assert (
        sort_order in SORT_ORDER_OPTIONS
    ), f"Error: sort_order should be one of {SORT_ORDER_OPTIONS}"
    assert offset >= 0, "Error: offset must be 0 or positive number"
    assert limit < 100, "Error: limit is too large, it should be less than 100"
    assert limit > 0, "Error: limit should be greater than 0"
    assert not _has_cyrillic(query), "Error: use only Latin script for queries"
    assert include_abstracts is not None, "Error: include_abstracts must be bool"

    fixed_query: str = _compose_query(query, start_date, end_date)
    url = URL_TEMPLATE.format(
        base_url=BASE_URL,
        query=fixed_query,
        start=offset,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    response = get_with_retries(url)
    content = response.content
    parsed_content = xmltodict.parse(content)

    feed = parsed_content.get("feed", {})
    total_results = int(feed.get("opensearch:totalResults", {}).get("#text", 0))
    start_index = int(feed.get("opensearch:startIndex", {}).get("#text", 0))
    entries = feed.get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]
    formatted_entries: str = _format_entries(
        entries,
        start_index=start_index,
        total_results=total_results,
        include_abstracts=include_abstracts,
    )
    return formatted_entries
