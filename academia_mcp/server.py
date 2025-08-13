import os
import socket
from typing import Optional

import fire  # type: ignore
import uvicorn
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from .tools.arxiv_search import arxiv_search
from .tools.arxiv_download import arxiv_download
from .tools.s2_citations import s2_get_citations, s2_get_references
from .tools.hf_datasets_search import hf_datasets_search
from .tools.anthology_search import anthology_search
from .tools.document_qa import create_document_qa_func
from .tools.md_to_pdf import md_to_pdf
from .tools.web_search import web_search

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
) -> None:
    server = FastMCP("Academia MCP", stateless_http=True)

    server.add_tool(arxiv_search)
    server.add_tool(arxiv_download)
    server.add_tool(s2_get_citations)
    server.add_tool(s2_get_references)
    server.add_tool(hf_datasets_search)
    server.add_tool(anthology_search)
    server.add_tool(md_to_pdf)
    server.add_tool(web_search)

    if api_key:
        server.add_tool(
            create_document_qa_func(api_key=api_key, base_url=base_url, model_name=model_name)
        )

    http_app = server.streamable_http_app()
    if port is None:
        port = find_free_port()
    uvicorn.run(http_app, host=host, port=port)


if __name__ == "__main__":
    fire.Fire(run)
