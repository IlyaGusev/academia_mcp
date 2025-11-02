import re
from typing import Any, Dict, List, Optional

from markdownify import markdownify  # type: ignore
from pydantic import BaseModel, Field

from academia_mcp.settings import settings
from academia_mcp.utils import get_with_retries, post_with_retries, sanitize_output

EXA_CONTENTS_URL = "https://api.exa.ai/contents"
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"
AVAILABLE_PROVIDERS = ("basic", "exa", "tavily")
ERROR_MESSAGE = "Failed to get content from the page. Try to use another provider."


class VisitWebpageResponse(BaseModel):  # type: ignore
    id: str = Field(description="ID of the webpage, usually the URL")
    provider: str = Field(description="Provider used to get the content")
    text: Optional[str] = Field(description="Text content of the webpage", default=None)
    images: List[str] = Field(description="Images of the webpage", default_factory=list)
    error: Optional[str] = Field(
        description="Error message if the webpage is not found", default=None
    )


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
    return {"text": results[0]["text"]}


def _tavily_visit_webpage(url: str) -> Dict[str, Any]:
    key = settings.TAVILY_API_KEY or ""
    assert key, "Error: TAVILY_API_KEY is not set and no api_key was provided"
    payload = {
        "urls": [url],
        "extract_depth": "advanced",
        "include_images": True,
    }
    response = post_with_retries(TAVILY_EXTRACT_URL, payload=payload, api_key=key)
    results = response.json()["results"]
    if not results:
        return {"error": ERROR_MESSAGE}
    result = results[0]
    return {"text": result["raw_content"], "images": result["images"]}


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


def visit_webpage(url: str, provider: str = "basic") -> VisitWebpageResponse:
    """
    Visit a webpage and return the content.
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

    result = VisitWebpageResponse(id=url, provider=provider, **result)
    if result.text:
        result.text = sanitize_output(result.text)
    if result.error:
        result.error = sanitize_output(result.error)
    return result
