import os
import re
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from typing import Any, List, Optional

from acl_anthology import Anthology
from pydantic import BaseModel, Field


class AnthologySingleton:
    instance: Optional[Anthology] = None

    @classmethod
    def get(cls) -> Anthology:
        if cls.instance is None:
            with open(os.devnull, "w") as devnull:
                with redirect_stdout(devnull), redirect_stderr(devnull):
                    cls.instance = Anthology.from_repo()
                    cls.instance.load_all()
        return cls.instance


SORT_BY_OPTIONS = ("relevance", "submittedDate", "published")
SORT_BY_MAPPING = {"submittedDate": "published"}
SORT_ORDER_OPTIONS = ("ascending", "descending")


class AnthologySearchEntry(BaseModel):  # type: ignore
    id: str = Field(description="ID of the paper")
    title: str = Field(description="Title of the paper")
    authors: str = Field(description="Authors of the paper")
    abstract: str = Field(description="Abstract of the paper")
    published_year: int = Field(description="Published year of the paper")
    categories: str = Field(description="Categories of the paper")
    comment: Optional[str] = Field(description="Comment of the paper", default=None)
    url: str = Field(description="URL of the paper")


class AnthologySearchResponse(BaseModel):  # type: ignore
    total_count: int = Field(description="Total number of results")
    returned_count: int = Field(description="Number of results returned")
    offset: int = Field(description="Offset for pagination")
    results: List[AnthologySearchEntry] = Field(description="Search entries")


def _format_text_field(text: str) -> str:
    return " ".join([line.strip() for line in text.split() if line.strip()])


def _format_authors(authors: List[Any]) -> str:
    names = [f"{author.name.first} {author.name.last}" for author in authors]
    result = ", ".join(names[:3])
    if len(names) > 3:
        result += f", and {len(names) - 3} more authors"
    return result


def _clean_entry(entry: Any) -> AnthologySearchEntry:
    return AnthologySearchEntry(
        id=entry.full_id,
        title=_format_text_field(entry.title.as_text()),
        authors=_format_authors(entry.authors),
        abstract=(_format_text_field(entry.abstract.as_text()) if entry.abstract else ""),
        published_year=entry.year,
        categories=", ".join(entry.venue_ids),
        comment=entry.note if entry.note else "",
        url=entry.pdf.url if entry.pdf and hasattr(entry.pdf, "url") else "",
    )


def _convert_to_year(date_str: str) -> int:
    try:
        return int(date_str[:4])
    except ValueError as e:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD format.") from e


def _has_cyrillic(text: str) -> bool:
    return bool(re.search("[а-яА-Я]", text))


def _parse_query(query: str, paper: Any) -> bool:
    conditions = re.split(r"\s+(AND|OR|ANDNOT)\s+", query)
    result = False
    for i in range(0, len(conditions), 2):
        condition = conditions[i]
        field, value = condition.split(":", 1) if ":" in condition else ("ti", condition)
        value = value.lower().replace('"', "").replace("'", "")
        match field:
            case "ti":
                match_found = value in paper.title.as_text().lower()
            case "au":
                match_found = any(value in str(author).lower() for author in paper.authors)
            case "abs":
                match_found = paper.abstract and value in paper.abstract.as_text().lower()
            case "cat":
                match_found = any(value in cat.lower() for cat in paper.venue_ids)
            case "id":
                match_found = value in paper.full_id.lower()
            case _:
                match_found = False
        if i == 0:
            result = match_found
        else:
            operator = conditions[i - 1]
            if operator == "AND":
                result = result and match_found
            elif operator == "OR":
                result = result or match_found
            elif operator == "ANDNOT":
                result = result and not match_found
    return result


def anthology_search(
    query: str,
    offset: int = 0,
    limit: int = 5,
    sort_by: str = "relevance",
    sort_order: str = "descending",
    include_abstracts: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> AnthologySearchResponse:
    """
    Search ACL Anthology papers with field-specific queries.

    Fields:
        all: (all fields), ti: (title), au: (author),
        abs: (abstract), cat: (category), id: (ID without version)

    Operators:
        AND, OR, ANDNOT

    Please always specify the fields. Search should always be field-specific.
    You can search for an exact match of an entire phrase by enclosing the phrase in double quotes.
    If you do not need an exact match of a phrase, use single terms with OR/AND.
    Boolean operators are strict. In most cases, you need OR and not AND.
    You can scroll all search results with the "offset" parameter.
    Do not include date constraints in the query: use "start_date" and "end_date" parameters instead.
    The names of authors should be in Latin script. For example, search "Ilya Gusev" instead of "Илья Гусев".

    Example queries:
        abs:"machine learning"
        au:"del maestro"
        au:vaswani AND ti:"attention is all"
        all:role OR all:playing OR all:"language model"
        (au:vaswani OR au:"del maestro") ANDNOT ti:attention

    Args:
        query: The search query, required.
        offset: The offset in search results. If it is 10, the first 10 items will be skipped. 0 by default.
        limit: The maximum number of items that will be returned. limit=5 by default, limit=10 is the maximum.
        sort_by: 3 options to sort by: relevance, lastUpdatedDate, submittedDate. relevance by default.
        sort_order: 2 sort orders: ascending, descending. descending by default.
        include_abstracts: include abstracts in the result or not. False by default.
        start_date: Start date in %Y-%m-%d format. None by default.
        end_date: End date in %Y-%m-%d format. None by default.
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

    sort_by = SORT_BY_MAPPING.get(sort_by, sort_by)

    singleton = AnthologySingleton.get()
    all_papers = [
        paper for paper in singleton.papers() if paper.abstract and str(paper.abstract).strip()
    ]

    if start_date or end_date:
        start_year = _convert_to_year(start_date) if start_date else 1900
        end_year = _convert_to_year(end_date) if end_date else datetime.now().year
        all_papers = [paper for paper in all_papers if start_year <= int(paper.year) <= end_year]

    filtered_papers = [paper for paper in all_papers if _parse_query(query, paper)]

    if sort_by == "published":
        filtered_papers.sort(key=lambda x: int(x.year), reverse=(sort_order == "descending"))

    paged_papers = filtered_papers[offset : offset + limit]
    clean_entries = [_clean_entry(entry) for entry in paged_papers]

    return AnthologySearchResponse(
        total_count=len(filtered_papers),
        returned_count=len(paged_papers),
        offset=offset,
        results=clean_entries,
    )
