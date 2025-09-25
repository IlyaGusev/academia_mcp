import re
import json
from typing import Optional, Dict, Any, cast

from markdownify import markdownify  # type: ignore

from academia_mcp.utils import get_with_retries, post_with_retries
from academia_mcp.settings import settings
from academia_mcp.utils import sanitize_output

EXA_CONTENTS_URL = "https://api.exa.ai/contents"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"
AVAILABLE_PROVIDERS = ("basic", "exa", "tavily")
ERROR_MESSAGE = "Failed to get content from the page. Try to use another provider."


def _exa_visit_webpage(url: str) -> Dict[str, Any]:
    key = settings.EXA_API_KEY or ""
    assert key, "Error: EXA_API_KEY is not set and no api_key was provided"
    payload = {
        "urls": [url],
        "text": True,
    }
    response = post_with_retries(EXA_CONTENTS_URL, payload=payload, api_key=key)
    results = response.json()["results"]
    if not results:
        return {"error": ERROR_MESSAGE}
    return cast(Dict[str, Any], results[0])


def _tavily_visit_webpage(url: str) -> Dict[str, Any]:
    key = settings.TAVILY_API_KEY or ""
    assert key, "Error: TAVILY_API_KEY is not set and no api_key was provided"
    payload = {
        "urls": [url],
    }
    response = post_with_retries(TAVILY_EXTRACT_URL, payload=payload, api_key=key)
    results = response.json()["results"]
    if not results:
        return {"error": ERROR_MESSAGE}
    return {"text": results[0]["raw_content"]}


def _basic_visit_webpage(url: str) -> Dict[str, Any]:
    try:
        response = get_with_retries(url)
        content_type = response.headers.get("content-type", "").lower()
        if not content_type or (
            not content_type.startswith("text/") and "html" not in content_type
        ):
            if settings.EXA_API_KEY:
                return _exa_visit_webpage(url)
            return {"error": f"Unsupported content-type: {content_type or 'unknown'}"}
        markdown_content = markdownify(response.text).strip()
        markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
        return {"text": markdown_content}
    except Exception as e:
        return {"error": str(e) + "\n" + ERROR_MESSAGE}


def visit_webpage(url: str, provider: Optional[str] = "basic") -> str:
    """
    Visit a webpage and return the content.

    Returns a JSON object serialized to a string. The structure is: {"id": "...", "text": "..."}.
    If there are errors, the structure is: {"id": "...", "error": "..."}.
    Use `json.loads` to deserialize the result if you want to get specific fields.
    Try to use both "tavily" and "basic" providers. They might work differently for the same URL.

    Args:
        url: The URL of the webpage to visit.
        provider: The provider to use. Available providers: "tavily" (default), "exa", or "basic".
    """
    assert (
        provider in AVAILABLE_PROVIDERS
    ), f"Invalid provider: {provider}. Available providers: {AVAILABLE_PROVIDERS}"

    if provider == "exa" and settings.EXA_API_KEY:
        result = _exa_visit_webpage(url)
    elif provider == "tavily" and settings.TAVILY_API_KEY:
        result = _tavily_visit_webpage(url)
    else:
        result = _basic_visit_webpage(url)

    result["id"] = url
    result["provider"] = provider
    return sanitize_output(json.dumps(result, ensure_ascii=False))
