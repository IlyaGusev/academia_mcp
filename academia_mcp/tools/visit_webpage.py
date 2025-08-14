import re
import os
import json
from typing import Optional

from markdownify import markdownify  # type: ignore

from academia_mcp.utils import get_with_retries, post_with_retries

EXA_CONTENTS_URL = "https://api.exa.ai/contents"
AVAILABLE_PROVIDERS = ("basic", "exa")


def visit_webpage(url: str, provider: Optional[str] = "basic") -> str:
    """
    Visit a webpage and return the content.

    Returns a JSON object serialized to a string. The structure is: {"url": "...", "text": "..."}
    Use `json.loads` to deserialize the result if you want to get specific fields.
    Use "exa" provider in case "basic" fails.

    Args:
        url: The URL of the webpage to visit.
        provider: The provider to use. Available providers: "basic" (default) or "exa".
    """
    assert (
        provider in AVAILABLE_PROVIDERS
    ), f"Invalid provider: {provider}. Available providers: {AVAILABLE_PROVIDERS}"

    if provider == "exa":
        key = os.getenv("EXA_API_KEY", "")
        assert key, "Error: EXA_API_KEY is not set and no api_key was provided"
        payload = {
            "urls": [url],
            "text": True,
        }
        response = post_with_retries(EXA_CONTENTS_URL, payload=payload, api_key=key)
        return json.dumps(response.json()["results"][0])

    assert provider == "basic"
    response = get_with_retries(url)
    markdown_content = markdownify(response.text).strip()
    markdown_content = re.sub(r"\n{3,}", "\n\n", markdown_content)
    return json.dumps({"id": url, "text": markdown_content})
