# Based on
# https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_get_paper_citations

from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from academia_mcp.utils import get_with_retries


PAPER_URL_TEMPLATE = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields={fields}"
CITATIONS_URL_TEMPLATE = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations?fields={fields}&offset={offset}&limit={limit}"
REFERENCES_URL_TEMPLATE = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references?fields={fields}&offset={offset}&limit={limit}"
FIELDS = "title,authors,externalIds,venue,citationCount,publicationDate"


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
    entry = entry["citingPaper"] if "citingPaper" in entry else entry["citedPaper"]
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
    offset: Optional[int] = 0,
    limit: Optional[int] = 50,
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

    url = CITATIONS_URL_TEMPLATE.format(
        paper_id=paper_id, fields=FIELDS, offset=offset, limit=limit
    )
    response = get_with_retries(url)
    result = response.json()
    entries = result["data"]
    total_count = len(result["data"]) + result["offset"]

    if "next" in result:
        paper_url = PAPER_URL_TEMPLATE.format(paper_id=paper_id, fields=FIELDS)
        paper_response = get_with_retries(paper_url)
        paper_result = paper_response.json()
        total_count = paper_result["citationCount"]

    return _format_entries(entries, offset if offset else 0, total_count)


def s2_get_references(
    arxiv_id: str,
    offset: Optional[int] = 0,
    limit: Optional[int] = 50,
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

    url = REFERENCES_URL_TEMPLATE.format(
        paper_id=paper_id, fields=FIELDS, offset=offset, limit=limit
    )
    response = get_with_retries(url)
    result = response.json()
    entries = result["data"]
    total_count = len(result["data"]) + result["offset"]
    return _format_entries(entries, offset if offset else 0, total_count)


def s2_corpus_id_from_arxiv_id(arxiv_id: str) -> int:
    """
    Get the S2 Corpus ID for a given arXiv ID.

    Args:
        arxiv_id: The ID of a given arXiv paper.
    """
    assert isinstance(arxiv_id, str), "Error: Your arxiv_id must be a string"
    if "v" in arxiv_id:
        arxiv_id = arxiv_id.split("v")[0]
    paper_url = PAPER_URL_TEMPLATE.format(paper_id=f"arxiv:{arxiv_id}", fields="externalIds")
    response = get_with_retries(paper_url)
    result = response.json()
    return int(result["externalIds"]["CorpusId"])


def s2_get_info(arxiv_id: str) -> S2PaperInfo:
    """
    Get the S2 info for a given arXiv ID.

    Args:
        arxiv_id: The ID of a given arXiv paper.
    """
    assert isinstance(arxiv_id, str), "Error: Your arxiv_id must be a string"
    if "v" in arxiv_id:
        arxiv_id = arxiv_id.split("v")[0]
    paper_url = PAPER_URL_TEMPLATE.format(paper_id=f"arxiv:{arxiv_id}", fields=FIELDS)
    response = get_with_retries(paper_url)
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
