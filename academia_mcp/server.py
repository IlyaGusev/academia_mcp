import os
import socket
from typing import Optional

import fire  # type: ignore
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from .tools.arxiv_search import arxiv_search
from .tools.arxiv_download import arxiv_download
from .tools.s2_citations import s2_get_citations, s2_get_references
from .tools.hf_datasets_search import hf_datasets_search
from .tools.anthology_search import anthology_search
from .tools.document_qa import create_document_qa_func
from .tools.md_to_pdf import md_to_pdf
from .tools.web_search import web_search, tavily_web_search, exa_web_search, brave_web_search
from .tools.visit_webpage import visit_webpage

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
MODEL_NAME = os.getenv("DOCUMENT_QA_MODEL_NAME", "gpt-4o-mini")


def find_free_port() -> int:
    for port in range(5000, 6001):
        try:
            with socket.socket() as s:
                s.bind(("", port))
                return port
        except Exception:
            continue
    return 5000


def run(
    host: str = "0.0.0.0",
    port: Optional[int] = None,
    api_key: str = API_KEY,
    base_url: str = BASE_URL,
    model_name: str = MODEL_NAME,
    mount_path: str = "/",
    streamable_http_path: str = "/mcp",
) -> None:
    server = FastMCP(
        "Academia MCP",
        stateless_http=True,
        streamable_http_path=streamable_http_path,
        mount_path=mount_path,
    )

    server.add_tool(arxiv_search)
    server.add_tool(arxiv_download)
    server.add_tool(s2_get_citations)
    server.add_tool(s2_get_references)
    server.add_tool(hf_datasets_search)
    server.add_tool(anthology_search)
    server.add_tool(md_to_pdf)
    if os.getenv("TAVILY_API_KEY"):
        server.add_tool(tavily_web_search)
    if os.getenv("EXA_API_KEY"):
        server.add_tool(exa_web_search)
    if os.getenv("BRAVE_API_KEY"):
        server.add_tool(brave_web_search)
    if os.getenv("EXA_API_KEY") or os.getenv("BRAVE_API_KEY") or os.getenv("TAVILY_API_KEY"):
        server.add_tool(web_search)
    server.add_tool(visit_webpage)

    if api_key:
        server.add_tool(
            create_document_qa_func(api_key=api_key, base_url=base_url, model_name=model_name)
        )

    if port is None:
        port = find_free_port()
    server.settings.port = port
    server.settings.host = host
    server.run(transport="streamable-http")


if __name__ == "__main__":
    fire.Fire(run)
