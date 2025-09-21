import re
import json
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional

import requests
from jinja2 import Template


def post_with_retries(
    url: str,
    payload: Dict[str, Any],
    api_key: Optional[str] = None,
    timeout: int = 30,
    num_retries: int = 3,
    backoff_factor: float = 3.0,
) -> requests.Response:
    retry_strategy = Retry(
        total=num_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {
        "x-api-key": api_key,
        "x-subscription-token": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = session.post(url, headers=headers, json=payload, timeout=timeout)
    response.raise_for_status()
    return response


def get_with_retries(
    url: str,
    api_key: Optional[str] = None,
    timeout: int = 30,
    num_retries: int = 3,
    backoff_factor: float = 3.0,
    params: Optional[Dict[str, Any]] = None,
) -> requests.Response:
    retry_strategy = Retry(
        total=num_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = {}
    if api_key:
        headers["x-api-key"] = api_key
        headers["x-subscription-token"] = api_key
        headers["Authorization"] = f"Bearer {api_key}"

    response = session.get(url, headers=headers, timeout=timeout, params=params)
    response.raise_for_status()
    return response


def clean_json_string(text: str) -> str:
    try:
        return json.dumps(json.loads(text))
    except json.JSONDecodeError:
        pass
    text = text.strip()
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    text = re.sub(r"'([^']*)':", r'"\1":', text)
    text = re.sub(r":\s*'([^']*)'", r': "\1"', text)
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)

    prefixes_to_remove = [
        "json:",
        "JSON:",
        "Here is the JSON:",
        "Here's the JSON:",
        "The JSON is:",
        "Result:",
        "Output:",
        "Response:",
    ]

    for prefix in prefixes_to_remove:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix) :].strip()

    return text


def extract_json(text: str) -> Any:
    assert isinstance(text, str), "Input must be a string"

    text = text.strip()
    assert text, "Input must be a non-empty string"

    json_blocks = re.findall(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    for block in json_blocks:
        try:
            return json.loads(block.strip())
        except json.JSONDecodeError:
            continue

    code_blocks = re.findall(r"```\s*(.*?)\s*```", text, re.DOTALL)
    for block in code_blocks:
        block = block.strip()
        if block.startswith(("{", "[")):
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue

    try:
        return json.loads(clean_json_string(text))
    except json.JSONDecodeError:
        pass

    json_patterns = [
        r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}",
        r"\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]",
        r"\{.*\}",
        r"\[.*\]",
    ]

    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in sorted(matches, key=len, reverse=True):
            try:
                cleaned = clean_json_string(match.strip())
                return json.loads(cleaned)
            except json.JSONDecodeError:
                continue

    return None


def encode_prompt(template: str, **kwargs: Any) -> str:
    template_obj = Template(template)
    return template_obj.render(**kwargs).strip()


def truncate_content(
    content: str,
    max_length: int,
) -> str:
    disclaimer = (
        f"\n\n..._This content has been truncated to stay below {max_length} characters_...\n\n"
    )
    half_length = max_length // 2
    if len(content) <= max_length:
        return content

    prefix = content[:half_length]
    suffix = content[-half_length:]
    return prefix + disclaimer + suffix


def sanitize_output(output: str) -> str:
    """
    See https://github.com/modelcontextprotocol/python-sdk/issues/1144#issuecomment-3076506124
    """
    output = output.replace("\x85", " ")
    output = output.replace("\u0085", " ")
    return output
