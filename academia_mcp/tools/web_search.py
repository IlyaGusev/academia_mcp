from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from academia_mcp.settings import settings
from academia_mcp.utils import get_with_retries, post_with_retries, sanitize_output

EXA_SEARCH_URL = "https://api.exa.ai/search"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
KEENABLE_SEARCH_URL = "https://api.keenable.ai/v1/search"
KEENABLE_SNIPPET_MAX_CHARS = 500
EXCLUDE_DOMAINS = ["chatpaper.com"]


def _parse_domains(query: str) -> Tuple[str, List[str]]:
    site_term = "site:"
    if site_term not in query:
        return query, []
    parts = query.split()
    query_parts = []
    include_domains = []
    for part in parts:
        if not part.startswith(site_term):
            query_parts.append(part)
            continue
        domain = part[len(site_term) :]
        if domain:
            include_domains.append(domain)
    query = " ".join(query_parts)
    return query, include_domains


class WebSearchEntry(BaseModel):  # type: ignore
    id: str = Field(description="ID of the search entry, usually the URL")
    title: str = Field(description="Title of the web page")
    content: str = Field(description="Content of the web page")


class WebSearchResponse(BaseModel):  # type: ignore
    results: List[WebSearchEntry] = Field(description="Results of the search")
    search_provider: str = Field(description="Provider used to get the results")


def web_search(
    query: str,
    limit: int = 20,
    provider: str = "tavily",
    include_domains: Optional[List[str]] = None,
) -> WebSearchResponse:
    """
    Search the web using Exa Search, Brave Search, Tavily or Keenable and return normalized results.
    If the specified provider is not available, the function will try to use the next available provider.

    Args:
        query: The search query, required.
        limit: The maximum number of items to return. 20 by default, maximum 25.
        provider: The provider to use. "exa", "tavily", "brave" or "keenable". "tavily" by default.
        include_domains: Optional list of domains to include in the search. None by default.
    """
    providers = ("tavily", "brave", "exa", "keenable")
    assert (
        provider in providers
    ), "Error: provider must be either 'exa', 'tavily', 'brave' or 'keenable'"
    if include_domains:
        assert len(include_domains) > 0, "Error: include_domains should be a non-empty list"
        assert all(
            isinstance(domain, str) for domain in include_domains
        ), "Error: include_domains should be a list of strings"

    query, query_include_domains = _parse_domains(query)
    if query_include_domains:
        if include_domains:
            include_domains.extend(query_include_domains)
        else:
            include_domains = query_include_domains

    is_tavily_available = bool(settings.TAVILY_API_KEY)
    is_exa_available = bool(settings.EXA_API_KEY)
    is_brave_available = bool(settings.BRAVE_API_KEY)
    is_keenable_available = bool(settings.KEENABLE_API_KEY)
    assert is_tavily_available or is_exa_available or is_brave_available or is_keenable_available
    availability = {
        "tavily": is_tavily_available,
        "brave": is_brave_available,
        "exa": is_exa_available,
        "keenable": is_keenable_available,
    }

    if not availability[provider]:
        for p in providers:
            if availability[p]:
                provider = p
                break

    result: Optional[WebSearchResponse] = None
    if provider == "exa":
        result = exa_web_search(query, limit, include_domains=include_domains)
    elif provider == "brave":
        result = brave_web_search(query, limit)
    elif provider == "tavily":
        result = tavily_web_search(query, limit, include_domains=include_domains)
    elif provider == "keenable":
        result = keenable_web_search(query, limit)
    assert result is not None, "Error: No provider was available"
    return result


def tavily_web_search(
    query: str, limit: int = 20, include_domains: Optional[List[str]] = None
) -> WebSearchResponse:
    """
    Search the web using Tavily and return results.

    Args:
        query: The search query, required.
        limit: The maximum number of items to return. 20 by default, maximum 25.
        include_domains: Optional list of domains to include in the search. None by default.
    """
    assert isinstance(query, str), "Error: Your search query must be a string"
    assert query.strip(), "Error: Your query should not be empty"
    assert isinstance(limit, int), "Error: limit should be an integer"
    assert 0 < limit <= 25, "Error: limit should be between 1 and 25"
    if include_domains:
        assert len(include_domains) > 0, "Error: include_domains should be a non-empty list"
        assert all(
            isinstance(domain, str) for domain in include_domains
        ), "Error: include_domains should be a list of strings"

    key = settings.TAVILY_API_KEY or ""
    assert key, "Error: TAVILY_API_KEY is not set and no api_key was provided"
    payload = {
        "query": query,
        "max_results": limit,
        "auto_parameters": True,
        "exclude_domains": EXCLUDE_DOMAINS,
    }
    if include_domains:
        payload["include_domains"] = include_domains
    response = post_with_retries(TAVILY_SEARCH_URL, payload, key)
    results = response.json()["results"]
    for result in results:
        content = " ".join(result["content"].split(" ")[:40])
        content = sanitize_output(content.strip("., "))
        result["content"] = content
        result.pop("raw_content", None)
        result.pop("score", None)
    entries = [
        WebSearchEntry(id=result["url"], title=result["title"], content=result["content"])
        for result in results
    ]
    return WebSearchResponse(results=entries, search_provider="tavily")


def exa_web_search(
    query: str, limit: int = 20, include_domains: Optional[List[str]] = None
) -> WebSearchResponse:
    """
    Search the web using Exa and return results.

    Args:
        query: The search query, required.
        limit: The maximum number of items to return. 20 by default, maximum 25.
        include_domains: Optional list of domains to include in the search. None by default.
    """
    assert isinstance(query, str), "Error: Your search query must be a string"
    assert query.strip(), "Error: Your query should not be empty"
    assert isinstance(limit, int), "Error: limit should be an integer"
    assert 0 < limit <= 25, "Error: limit should be between 1 and 25"
    if include_domains:
        assert len(include_domains) > 0, "Error: include_domains should be a non-empty list"
        assert all(
            isinstance(domain, str) for domain in include_domains
        ), "Error: include_domains should be a list of strings"

    key = settings.EXA_API_KEY or ""
    assert key, "Error: EXA_API_KEY is not set and no api_key was provided"
    payload = {
        "query": query,
        "type": "auto",
        "numResults": limit,
        "context": False,
        "excludeDomains": EXCLUDE_DOMAINS,
        "contents": {
            "text": False,
            "highlights": {
                "numSentences": 5,
            },
            "context": False,
        },
    }
    if include_domains:
        payload["includeDomains"] = include_domains

    response = post_with_retries(EXA_SEARCH_URL, payload, key)
    results = response.json()["results"]
    entries = []
    for result in results:
        content = " || ".join(result["highlights"])
        content = sanitize_output(content)
        entries.append(WebSearchEntry(id=result["url"], title=result["title"], content=content))
    return WebSearchResponse(results=entries, search_provider="exa")


def brave_web_search(
    query: str, limit: int = 20, extra_snippets: bool = False
) -> WebSearchResponse:
    """
    Search the web using Brave and return results.

    Args:
        query: The search query, required.
        limit: The maximum number of items to return. 20 by default, maximum 20.
        extra_snippets: Include extra snippets in the content. False by default.
    """
    assert isinstance(query, str), "Error: Your search query must be a string"
    assert query.strip(), "Error: Your query should not be empty"
    assert isinstance(limit, int), "Error: limit should be an integer"
    assert 0 < limit <= 20, "Error: limit should be between 1 and 20"

    key = settings.BRAVE_API_KEY or ""
    assert key, "Error: BRAVE_API_KEY is not set and no api_key was provided"
    payload = {"q": query, "count": limit, "extra_snippets": extra_snippets}
    response = get_with_retries(BRAVE_SEARCH_URL, key, params=payload)
    results = response.json()["web"]["results"]
    entries = []
    for result in results:
        content = str(result["description"])
        if extra_snippets and "extra_snippets" in result:
            content += "\n\nExtra snippets:\n" + "\n".join(result["extra_snippets"])
        content = sanitize_output(content)
        entries.append(WebSearchEntry(id=result["url"], title=result["title"], content=content))
    return WebSearchResponse(results=entries, search_provider="brave")


def keenable_web_search(query: str, limit: int = 20) -> WebSearchResponse:
    """
    Search the web using Keenable and return results.

    Args:
        query: The search query, required.
        limit: The maximum number of items to return. 20 by default, maximum 20.
    """
    assert isinstance(query, str), "Error: Your search query must be a string"
    assert query.strip(), "Error: Your query should not be empty"
    assert isinstance(limit, int), "Error: limit should be an integer"
    assert 0 < limit <= 20, "Error: limit should be between 1 and 20"

    key = settings.KEENABLE_API_KEY or ""
    assert key, "Error: KEENABLE_API_KEY is not set and no api_key was provided"
    payload = {"query": query, "max_results": limit}
    response = post_with_retries(
        KEENABLE_SEARCH_URL,
        payload,
        key,
        extra_headers={"X-API-Key": key, "X-Keenable-Title": "Academia MCP"},
    )
    results = response.json().get("results") or []
    entries = []
    for result in results:
        url = result.get("url")
        if not url:
            continue
        content = (
            result.get("description") or (result.get("snippet") or "")[:KEENABLE_SNIPPET_MAX_CHARS]
        )
        entries.append(
            WebSearchEntry(
                id=url, title=result.get("title") or "", content=sanitize_output(content)
            )
        )
    return WebSearchResponse(results=entries, search_provider="keenable")
