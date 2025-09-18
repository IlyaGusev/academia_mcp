# Based on
# https://api.semanticscholar.org/api-docs/graph#tag/Paper-Data/operation/get_graph_get_paper_citations

import json
from typing import Optional, List, Dict, Any

from academia_mcp.utils import get_with_retries


PAPER_URL_TEMPLATE = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}?fields={fields}"
CITATIONS_URL_TEMPLATE = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations?fields={fields}&offset={offset}&limit={limit}"
REFERENCES_URL_TEMPLATE = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}/references?fields={fields}&offset={offset}&limit={limit}"
FIELDS = "title,authors,externalIds,venue,citationCount,publicationDate"


def _format_authors(authors: List[Dict[str, Any]]) -> List[str]:
    return [a["name"] for a in authors]


def _clean_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    entry = entry["citingPaper"] if "citingPaper" in entry else entry["citedPaper"]
    external_ids = entry.get("externalIds")
    if not external_ids:
        external_ids = dict()
    external_ids.pop("CorpusId", None)
    arxiv_id = external_ids.pop("ArXiv", None)
    return {
        "arxiv_id": arxiv_id,
        "external_ids": external_ids if external_ids else None,
        "title": entry["title"],
        "authors": _format_authors(entry["authors"]),
        "venue": entry.get("venue", ""),
        "citation_count": entry.get("citationCount", 0),
        "publication_date": entry.get("publicationDate", ""),
    }


def _format_entries(
    entries: List[Dict[str, Any]],
    start_index: int,
    total_results: int,
) -> str:
    clean_entries = [_clean_entry(e) for e in entries]
    return json.dumps(
        {
            "total_count": total_results,
            "returned_count": len(entries),
            "offset": start_index,
            "results": clean_entries,
        },
        ensure_ascii=False,
    )


def s2_get_citations(
    arxiv_id: str,
    offset: Optional[int] = 0,
    limit: Optional[int] = 50,
) -> str:
    """
    Get all papers that cited a given arXiv paper based on Semantic Scholar info.

    Returns a JSON object serialized to a string. The structure is:
    {"total_count": ..., "returned_count": ..., "offset": ..., "results": [...]}
    Every item in the "results" has the following fields:
    ("arxiv_id", "external_ids", "title", "authors", "venue", "citation_count", "publication_date")
    Use `json.loads` to deserialize the result if you want to get specific fields.

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
) -> str:
    """
    Get all papers that were cited by a given arXiv paper (references) based on Semantic Scholar info.

    Returns a JSON object serialized to a string. The structure is:
    {"total_count": ..., "returned_count": ..., "offset": ..., "results": [...]}
    Every item in the "results" has the following fields:
    ("arxiv_id", "external_ids", "title", "authors", "venue", "citation_count", "publication_date")
    Use `json.loads` to deserialize the result if you want to get specific fields.

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


def s2_get_info(arxiv_id: str) -> str:
    """
    Get the S2 info for a given arXiv ID.

    Returns a JSON object serialized to a string. The structure is:
    {"title": ..., "authors": ..., "externalIds": ..., "venue": ..., "citationCount": ..., "publicationDate": ...}
    Use `json.loads` to deserialize the result if you want to get specific fields.

    Args:
        arxiv_id: The ID of a given arXiv paper.
    """
    assert isinstance(arxiv_id, str), "Error: Your arxiv_id must be a string"
    if "v" in arxiv_id:
        arxiv_id = arxiv_id.split("v")[0]
    paper_url = PAPER_URL_TEMPLATE.format(paper_id=f"arxiv:{arxiv_id}", fields=FIELDS)
    response = get_with_retries(paper_url)
    return json.dumps(response.json(), ensure_ascii=False)
