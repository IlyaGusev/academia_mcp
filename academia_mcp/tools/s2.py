# Based on
# https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_get_paper_citations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from academia_mcp.utils import get_with_retries

BASE_URL = "https://api.semanticscholar.org/graph/v1"
PAPER_URL_TEMPLATE = "{base_url}/paper/{paper_id}"
CITATIONS_URL_TEMPLATE = "{base_url}/paper/{paper_id}/citations"
REFERENCES_URL_TEMPLATE = "{base_url}/paper/{paper_id}/references"
SEARCH_URL_TEMPLATE = "{base_url}/paper/search"
FIELDS = "paperId,title,authors,externalIds,venue,citationCount,publicationDate"


class S2PaperInfo(BaseModel):  # type: ignore
    arxiv_id: Optional[str] = Field(description="ArXiv ID of the paper", default=None)
    external_ids: Optional[Dict[str, Any]] = Field(
        description="External IDs of the paper.", default=None
    )
    title: str = Field(description="Paper title")
    authors: List[str] = Field(description="Authors of the paper")
    venue: str = Field(description="Paper venue")
    citation_count: Optional[int] = Field(description="Paper citation count", default=None)
    publication_date: Optional[str] = Field(description="Paper publication date", default=None)


class S2SearchResponse(BaseModel):  # type: ignore
    total_count: int = Field(description="Total number of results.")
    returned_count: int = Field(description="Number of results returned.")
    offset: int = Field(description="Offset of the results.")
    results: List[S2PaperInfo] = Field(description="Search entries")


def _format_authors(authors: List[Dict[str, Any]]) -> List[str]:
    return [a["name"] for a in authors]


def _clean_entry(entry: Dict[str, Any]) -> S2PaperInfo:
    if "citingPaper" in entry:
        entry = entry["citingPaper"]
    elif "citedPaper" in entry:
        entry = entry["citedPaper"]
    external_ids = entry.get("externalIds")
    if not external_ids:
        external_ids = dict()
    external_ids.pop("CorpusId", None)
    arxiv_id = external_ids.pop("ArXiv", None)
    return S2PaperInfo(
        arxiv_id=arxiv_id,
        external_ids=external_ids if external_ids else None,
        title=entry["title"],
        authors=_format_authors(entry["authors"]),
        venue=entry.get("venue", ""),
        citation_count=entry.get("citationCount"),
        publication_date=entry.get("publicationDate"),
    )


def _format_entries(
    entries: List[Dict[str, Any]],
    start_index: int,
    total_results: int,
) -> S2SearchResponse:
    clean_entries = [_clean_entry(e) for e in entries]
    return S2SearchResponse(
        total_count=total_results,
        returned_count=len(entries),
        offset=start_index,
        results=clean_entries,
    )


def s2_get_citations(
    arxiv_id: str,
    offset: int = 0,
    limit: int = 50,
) -> S2SearchResponse:
    """
    Get all papers that cited a given arXiv paper based on Semantic Scholar info.

    Args:
        arxiv_id: The ID of a given arXiv paper.
        offset: The offset to scroll through citations. 10 items will be skipped if offset=10. 0 by default.
        limit: The maximum number of items to return. limit=50 by default.
    """

    assert isinstance(arxiv_id, str), "Error: Your arxiv_id must be a string"
    if "v" in arxiv_id:
        arxiv_id = arxiv_id.split("v")[0]
    paper_id = f"arxiv:{arxiv_id}"

    url = CITATIONS_URL_TEMPLATE.format(base_url=BASE_URL, paper_id=paper_id)
    payload = {"fields": FIELDS, "offset": offset, "limit": limit}
    response = get_with_retries(url, params=payload)
    result = response.json()
    entries = result["data"]
    total_count = len(result["data"]) + result["offset"]

    if "next" in result:
        paper_url = PAPER_URL_TEMPLATE.format(base_url=BASE_URL, paper_id=paper_id)
        payload = {"fields": FIELDS}
        paper_response = get_with_retries(paper_url, params=payload)
        paper_result = paper_response.json()
        total_count = paper_result["citationCount"]

    return _format_entries(entries, offset if offset else 0, total_count)


def s2_get_references(
    arxiv_id: str,
    offset: int = 0,
    limit: int = 50,
) -> S2SearchResponse:
    """
    Get all papers that were cited by a given arXiv paper (references) based on Semantic Scholar info.

    Args:
        arxiv_id: The ID of a given arXiv paper.
        offset: The offset to scroll through citations. 10 items will be skipped if offset=10. 0 by default.
        limit: The maximum number of items to return. limit=50 by default.
    """
    assert isinstance(arxiv_id, str), "Error: Your arxiv_id must be a string"
    if "v" in arxiv_id:
        arxiv_id = arxiv_id.split("v")[0]
    paper_id = f"arxiv:{arxiv_id}"

    url = REFERENCES_URL_TEMPLATE.format(base_url=BASE_URL, paper_id=paper_id)
    payload = {"fields": FIELDS, "offset": offset, "limit": limit}
    response = get_with_retries(url, params=payload)
    result = response.json()
    entries = result["data"]
    total_count = len(result["data"]) + result["offset"]
    return _format_entries(entries, offset if offset else 0, total_count)


def s2_get_info(arxiv_id: str) -> S2PaperInfo:
    """
    Get the S2 info for a given arXiv ID.

    Args:
        arxiv_id: The ID of a given arXiv paper.
    """
    assert isinstance(arxiv_id, str), "Error: Your arxiv_id must be a string"
    if "v" in arxiv_id:
        arxiv_id = arxiv_id.split("v")[0]
    paper_id = f"arxiv:{arxiv_id}"
    payload = {"fields": FIELDS}
    paper_url = PAPER_URL_TEMPLATE.format(base_url=BASE_URL, paper_id=paper_id)
    response = get_with_retries(paper_url, params=payload)
    json_data = response.json()
    return S2PaperInfo(
        arxiv_id=json_data.get("externalIds", {}).get("ArXiv"),
        external_ids=json_data.get("externalIds", {}),
        title=json_data["title"],
        authors=_format_authors(json_data["authors"]),
        venue=json_data.get("venue", ""),
        citation_count=int(json_data.get("citationCount", 0)),
        publication_date=str(json_data.get("publicationDate", "")),
    )


def s2_search(
    query: str,
    offset: int = 0,
    limit: int = 5,
    min_citation_count: int = 0,
    publication_date: Optional[str] = None,
) -> S2SearchResponse:
    """
    Search the S2 corpus for a given query.

    Args:
        query: The query to search for.
        offset: The offset to scroll through results. 10 items will be skipped if offset=10. 0 by default.
        limit: The maximum number of items to return. limit=50 by default.
        min_citation_count: The minimum citation count to return. 0 by default.
        publication_date: Restricts results to the given range of publication dates or years (inclusive).
            Accepts the format <startDate>:<endDate> with each date in YYYY-MM-DD format. None by default.
    """
    url = SEARCH_URL_TEMPLATE.format(base_url=BASE_URL)
    payload = {
        "query": query,
        "offset": offset,
        "limit": limit,
        "minCitationCount": min_citation_count,
        "fields": FIELDS,
    }
    if publication_date:
        payload["publicationDateOrYear"] = publication_date
    response = get_with_retries(url, params=payload, backoff_factor=10.0, num_retries=5)
    result = response.json()
    if "data" not in result:
        return S2SearchResponse(
            total_count=0,
            returned_count=0,
            offset=offset if offset else 0,
            results=[],
        )
    entries = result["data"]
    total_count = result["total"]
    return _format_entries(entries, offset if offset else 0, total_count)
