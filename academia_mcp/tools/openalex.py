from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from academia_mcp.utils import get_with_retries

BASE_URL = "https://api.openalex.org"
WORKS_SEARCH_URL = f"{BASE_URL}/works"
WORK_URL_TEMPLATE = f"{BASE_URL}/works/{{work_id}}"
AUTHORS_SEARCH_URL = f"{BASE_URL}/authors"
AUTHOR_URL_TEMPLATE = f"{BASE_URL}/authors/{{author_id}}"
INSTITUTION_URL_TEMPLATE = f"{BASE_URL}/institutions/{{institution_id}}"


class OpenAlexAuthorInfo(BaseModel):  # type: ignore
    id: str = Field(description="OpenAlex author ID")
    name: str = Field(description="Author name")
    orcid: Optional[str] = Field(description="ORCID identifier", default=None)


class OpenAlexWorkEntry(BaseModel):  # type: ignore
    id: str = Field(description="OpenAlex work ID")
    doi: Optional[str] = Field(description="DOI of the work", default=None)
    title: str = Field(description="Title of the work")
    authors: List[str] = Field(description="Authors of the work")
    publication_year: Optional[int] = Field(description="Publication year", default=None)
    publication_date: Optional[str] = Field(description="Publication date", default=None)
    venue: Optional[str] = Field(description="Publication venue", default=None)
    cited_by_count: int = Field(description="Number of citations", default=0)
    abstract: Optional[str] = Field(description="Abstract of the work", default=None)
    topics: List[str] = Field(description="Topics associated with the work", default_factory=list)


class OpenAlexSearchResponse(BaseModel):  # type: ignore
    total_count: int = Field(description="Total number of results")
    returned_count: int = Field(description="Number of results returned")
    offset: int = Field(description="Offset for pagination")
    results: List[OpenAlexWorkEntry] = Field(description="Search results")


class OpenAlexAuthorEntry(BaseModel):  # type: ignore
    id: str = Field(description="OpenAlex author ID")
    name: str = Field(description="Author name")
    orcid: Optional[str] = Field(description="ORCID identifier", default=None)
    works_count: int = Field(description="Number of works", default=0)
    cited_by_count: int = Field(description="Total citation count", default=0)
    h_index: Optional[int] = Field(description="H-index", default=None)
    i10_index: Optional[int] = Field(description="i10-index", default=None)
    affiliations: List[str] = Field(description="Current affiliations", default_factory=list)


class OpenAlexAuthorSearchResponse(BaseModel):  # type: ignore
    total_count: int = Field(description="Total number of results")
    returned_count: int = Field(description="Number of results returned")
    offset: int = Field(description="Offset for pagination")
    results: List[OpenAlexAuthorEntry] = Field(description="Search results")


class OpenAlexInstitutionInfo(BaseModel):  # type: ignore
    id: str = Field(description="OpenAlex institution ID")
    name: str = Field(description="Institution name")
    ror: Optional[str] = Field(description="ROR identifier", default=None)
    country_code: Optional[str] = Field(description="Country code", default=None)
    type: Optional[str] = Field(description="Institution type", default=None)
    works_count: int = Field(description="Number of works", default=0)
    cited_by_count: int = Field(description="Total citation count", default=0)


def _format_authors(authors_list: List[Dict[str, Any]]) -> List[str]:
    names = []
    for author_data in authors_list:
        author = author_data.get("author", {})
        name = author.get("display_name", "Unknown")
        names.append(name)
    if len(names) > 10:
        return names[:10] + [f"and {len(names) - 10} more authors"]
    return names


def _extract_work_info(work: Dict[str, Any]) -> OpenAlexWorkEntry:
    abstract = None
    if work.get("abstract_inverted_index"):
        inverted_index = work["abstract_inverted_index"]
        word_positions = []
        for word, positions in inverted_index.items():
            for pos in positions:
                word_positions.append((pos, word))
        word_positions.sort()
        abstract = " ".join([word for _, word in word_positions])

    topics = []
    for topic_data in work.get("topics", [])[:5]:
        if "display_name" in topic_data:
            topics.append(topic_data["display_name"])

    venue_name = None
    primary_location = work.get("primary_location")
    if primary_location and primary_location.get("source"):
        venue_name = primary_location["source"].get("display_name")

    return OpenAlexWorkEntry(
        id=work.get("id", ""),
        doi=work.get("doi"),
        title=work.get("title", ""),
        authors=_format_authors(work.get("authorships", [])),
        publication_year=work.get("publication_year"),
        publication_date=work.get("publication_date"),
        venue=venue_name,
        cited_by_count=work.get("cited_by_count", 0),
        abstract=abstract,
        topics=topics,
    )


def _extract_author_info(author: Dict[str, Any]) -> OpenAlexAuthorEntry:
    affiliations = []
    for affiliation_data in author.get("affiliations", [])[:3]:
        institution = affiliation_data.get("institution", {})
        name = institution.get("display_name")
        if name:
            affiliations.append(name)

    summary_stats = author.get("summary_stats", {})

    return OpenAlexAuthorEntry(
        id=author.get("id", ""),
        name=author.get("display_name", ""),
        orcid=author.get("orcid"),
        works_count=author.get("works_count", 0),
        cited_by_count=author.get("cited_by_count", 0),
        h_index=summary_stats.get("h_index"),
        i10_index=summary_stats.get("i10_index"),
        affiliations=affiliations,
    )


def openalex_search_works(
    query: str,
    offset: int = 0,
    limit: int = 10,
    sort_by: str = "relevance",
    min_cited_by_count: int = 0,
    publication_year: Optional[str] = None,
) -> OpenAlexSearchResponse:
    """
    Search OpenAlex for works (papers, books, etc.) matching a query.

    Supports filtering by publication year and citation count.
    Results include title, authors, abstract, venue, citations, and topics.

    Args:
        query: Search query string.
        offset: Offset for pagination. 0 by default.
        limit: Maximum number of results to return. 10 by default, 200 maximum.
        sort_by: Sort order. Options: relevance, cited_by_count, publication_date. Default: relevance.
        min_cited_by_count: Minimum citation count filter. 0 by default.
        publication_year: Filter by publication year. Format: single year (2020) or range (2020-2023).
    """
    assert isinstance(query, str), "query must be a string"
    assert query.strip(), "query cannot be empty"
    assert isinstance(offset, int) and offset >= 0, "offset must be non-negative integer"
    assert isinstance(limit, int) and 0 < limit <= 200, "limit must be between 1 and 200"
    assert sort_by in [
        "relevance",
        "cited_by_count",
        "publication_date",
    ], "Invalid sort_by option"

    params: Dict[str, Any] = {
        "search": query,
        "page": (offset // limit) + 1,
        "per_page": limit,
    }

    if sort_by == "relevance":
        params["sort"] = "relevance_score:desc"
    elif sort_by == "cited_by_count":
        params["sort"] = "cited_by_count:desc"
    elif sort_by == "publication_date":
        params["sort"] = "publication_date:desc"

    filter_parts = []
    if min_cited_by_count > 0:
        filter_parts.append(f"cited_by_count:>{min_cited_by_count - 1}")

    if publication_year:
        if "-" in publication_year:
            start_year, end_year = publication_year.split("-")
            filter_parts.append(f"publication_year:{start_year}-{end_year}")
        else:
            filter_parts.append(f"publication_year:{publication_year}")

    if filter_parts:
        params["filter"] = ",".join(filter_parts)

    response = get_with_retries(WORKS_SEARCH_URL, params=params)
    data = response.json()

    results = [_extract_work_info(work) for work in data.get("results", [])]
    meta = data.get("meta", {})

    return OpenAlexSearchResponse(
        total_count=meta.get("count", 0),
        returned_count=len(results),
        offset=offset,
        results=results,
    )


def openalex_get_work(work_id: str) -> OpenAlexWorkEntry:
    """
    Get detailed information about a specific work by OpenAlex ID or DOI.

    Args:
        work_id: OpenAlex work ID (e.g., W2741809807) or DOI (e.g., 10.1371/journal.pone.0000000).
            DOIs can be prefixed with 'doi:' or 'https://doi.org/'.
    """
    assert isinstance(work_id, str), "work_id must be a string"
    assert work_id.strip(), "work_id cannot be empty"

    if work_id.startswith("10."):
        work_id = f"https://doi.org/{work_id}"

    url = WORK_URL_TEMPLATE.format(work_id=work_id)
    response = get_with_retries(url)
    work = response.json()

    return _extract_work_info(work)


def openalex_search_authors(
    query: str,
    offset: int = 0,
    limit: int = 10,
) -> OpenAlexAuthorSearchResponse:
    """
    Search OpenAlex for authors matching a query.

    Returns author information including name, ORCID, citation metrics, and affiliations.

    Args:
        query: Search query string (author name).
        offset: Offset for pagination. 0 by default.
        limit: Maximum number of results to return. 10 by default, 200 maximum.
    """
    assert isinstance(query, str), "query must be a string"
    assert query.strip(), "query cannot be empty"
    assert isinstance(offset, int) and offset >= 0, "offset must be non-negative integer"
    assert isinstance(limit, int) and 0 < limit <= 200, "limit must be between 1 and 200"

    params: Dict[str, Any] = {
        "search": query,
        "page": (offset // limit) + 1,
        "per_page": limit,
    }

    response = get_with_retries(AUTHORS_SEARCH_URL, params=params)
    data = response.json()

    results = [_extract_author_info(author) for author in data.get("results", [])]
    meta = data.get("meta", {})

    return OpenAlexAuthorSearchResponse(
        total_count=meta.get("count", 0),
        returned_count=len(results),
        offset=offset,
        results=results,
    )


def openalex_get_author(author_id: str) -> OpenAlexAuthorEntry:
    """
    Get detailed information about a specific author by OpenAlex ID or ORCID.

    Args:
        author_id: OpenAlex author ID (e.g., A2208157607) or ORCID (e.g., 0000-0001-6187-6610).
            ORCIDs can be prefixed with 'orcid:' or 'https://orcid.org/'.
    """
    assert isinstance(author_id, str), "author_id must be a string"
    assert author_id.strip(), "author_id cannot be empty"

    if author_id.startswith("0000-"):
        author_id = f"orcid:{author_id}"
    elif author_id.startswith("https://orcid.org/"):
        author_id = author_id.replace("https://orcid.org/", "orcid:")

    url = AUTHOR_URL_TEMPLATE.format(author_id=author_id)
    response = get_with_retries(url)
    author = response.json()

    return _extract_author_info(author)


def openalex_get_institution(institution_id: str) -> OpenAlexInstitutionInfo:
    """
    Get detailed information about a specific institution by OpenAlex ID or ROR.

    Args:
        institution_id: OpenAlex institution ID (e.g., I136199984) or ROR (e.g., 03yrm5c26).
            RORs can be prefixed with 'ror:' or 'https://ror.org/'.
    """
    assert isinstance(institution_id, str), "institution_id must be a string"
    assert institution_id.strip(), "institution_id cannot be empty"

    if institution_id.startswith("https://ror.org/"):
        institution_id = institution_id.replace("https://ror.org/", "ror:")
    elif not institution_id.startswith(("I", "ror:")):
        institution_id = f"ror:{institution_id}"

    url = INSTITUTION_URL_TEMPLATE.format(institution_id=institution_id)
    response = get_with_retries(url)
    institution = response.json()

    return OpenAlexInstitutionInfo(
        id=institution.get("id", ""),
        name=institution.get("display_name", ""),
        ror=institution.get("ror"),
        country_code=institution.get("country_code"),
        type=institution.get("type"),
        works_count=institution.get("works_count", 0),
        cited_by_count=institution.get("cited_by_count", 0),
    )
