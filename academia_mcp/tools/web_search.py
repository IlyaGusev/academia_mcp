import json
from typing import Optional

from academia_mcp.utils import post_with_retries, get_with_retries
from academia_mcp.settings import settings
from academia_mcp.utils import sanitize_output


EXA_SEARCH_URL = "https://api.exa.ai/search"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"
BRAVE_SEARCH_URL = "https://api.search.brave.com/res/v1/web/search"
EXCLUDE_DOMAINS = ["chatpaper.com"]


def web_search(
    query: str,
    limit: Optional[int] = 20,
    provider: Optional[str] = "tavily",
) -> str:
    """
    Search the web using Exa Search, Brave Search or Tavily and return normalized results.
    If the specified provider is not available, the function will try to use the next available provider.

    Returns a JSON object serialized to a string. The structure is: {"results": [...]}
    Every item in the "results" has at least the following fields: ("title", "url")
    Use `json.loads` to deserialize the result if you want to get specific fields.

    Args:
        query: The search query, required.
        limit: The maximum number of items to return. 20 by default, maximum 25.
        provider: The provider to use. "exa", "tavily" or "brave". "tavily" by default.
    """
    providers = ("tavily", "brave", "exa")
    assert provider in providers, "Error: provider must be either 'exa', 'tavily' or 'brave'"

    is_tavily_available = bool(settings.TAVILY_API_KEY)
    is_exa_available = bool(settings.EXA_API_KEY)
    is_brave_available = bool(settings.BRAVE_API_KEY)
    assert is_tavily_available or is_exa_available or is_brave_available
    availability = {
        "tavily": is_tavily_available,
        "brave": is_brave_available,
        "exa": is_exa_available,
    }

    if not availability[provider]:
        for p in providers:
            if availability[p]:
                provider = p
                break

    result = {}
    if provider == "exa":
        result = json.loads(exa_web_search(query, limit))
    elif provider == "brave":
        result = json.loads(brave_web_search(query, limit))
    elif provider == "tavily":
        result = json.loads(tavily_web_search(query, limit))
    result["search_provider"] = provider
    return sanitize_output(json.dumps(result, ensure_ascii=False))


def tavily_web_search(query: str, limit: Optional[int] = 20) -> str:
    """
    Search the web using Tavily and return results.

    Returns a JSON object serialized to a string. The structure is: {"results": [...]}
    Every item in the "results" has at least the following fields: ("title", "url")
    Use `json.loads` to deserialize the result if you want to get specific fields.

    Args:
        query: The search query, required.
        limit: The maximum number of items to return. 20 by default, maximum 25.
    """
    assert isinstance(query, str), "Error: Your search query must be a string"
    assert query.strip(), "Error: Your query should not be empty"
    assert isinstance(limit, int), "Error: limit should be an integer"
    assert 0 < limit <= 25, "Error: limit should be between 1 and 25"

    key = settings.TAVILY_API_KEY or ""
    assert key, "Error: TAVILY_API_KEY is not set and no api_key was provided"
    payload = {
        "query": query,
        "max_results": limit,
        "auto_parameters": True,
        "exclude_domains": EXCLUDE_DOMAINS,
    }
    response = post_with_retries(TAVILY_SEARCH_URL, payload, key)
    results = response.json()["results"]
    for result in results:
        content = " ".join(result["content"].split(" ")[:40])
        content = content.strip("., ")
        result["content"] = content
        result.pop("raw_content", None)
        result.pop("score", None)
    return sanitize_output(json.dumps({"results": results}, ensure_ascii=False))


def exa_web_search(query: str, limit: Optional[int] = 20) -> str:
    """
    Search the web using Exa and return results.

    Returns a JSON object serialized to a string. The structure is: {"results": [...]}
    Every item in the "results" has at least the following fields: ("title", "url")
    Use `json.loads` to deserialize the result if you want to get specific fields.

    Args:
        query: The search query, required.
        limit: The maximum number of items to return. 20 by default, maximum 25.
    """
    assert isinstance(query, str), "Error: Your search query must be a string"
    assert query.strip(), "Error: Your query should not be empty"
    assert isinstance(limit, int), "Error: limit should be an integer"
    assert 0 < limit <= 25, "Error: limit should be between 1 and 25"

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

    response = post_with_retries(EXA_SEARCH_URL, payload, key)
    results = response.json()["results"]
    return sanitize_output(json.dumps({"results": results}, ensure_ascii=False))


def brave_web_search(query: str, limit: Optional[int] = 20) -> str:
    """
    Search the web using Brave and return results.

    Returns a JSON object serialized to a string. The structure is: {"results": [...]}
    Every item in the "results" has at least the following fields: ("title", "url")
    Use `json.loads` to deserialize the result if you want to get specific fields.

    Args:
        query: The search query, required.
        limit: The maximum number of items to return. 20 by default, maximum 20.
    """
    assert isinstance(query, str), "Error: Your search query must be a string"
    assert query.strip(), "Error: Your query should not be empty"
    assert isinstance(limit, int), "Error: limit should be an integer"
    assert 0 < limit <= 20, "Error: limit should be between 1 and 20"

    key = settings.BRAVE_API_KEY or ""
    assert key, "Error: BRAVE_API_KEY is not set and no api_key was provided"
    payload = {
        "q": query,
        "count": limit,
    }
    response = get_with_retries(BRAVE_SEARCH_URL, key, params=payload)
    results = response.json()["web"]["results"]
    return sanitize_output(json.dumps({"results": results}, ensure_ascii=False))
