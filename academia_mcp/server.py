import os
import socket
from typing import Optional, Literal

import fire  # type: ignore
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from .tools.arxiv_search import arxiv_search
from .tools.arxiv_download import arxiv_download
from .tools.s2_citations import s2_get_citations, s2_get_references
from .tools.hf_datasets_search import hf_datasets_search
from .tools.anthology_search import anthology_search
from .tools.document_qa import document_qa
from .tools.latex import (
    compile_latex_from_file,
    compile_latex_from_str,
    get_latex_template,
    get_latex_templates_list,
    read_pdf,
)
from .tools.web_search import web_search, tavily_web_search, exa_web_search, brave_web_search
from .tools.visit_webpage import visit_webpage
from .tools.bitflip import (
    extract_bitflip_info,
    generate_research_proposals,
    score_research_proposals,
)
from .tools.review import review_pdf_paper, download_pdf_paper


load_dotenv()


def find_free_port() -> int:
    for port in range(5000, 6001):
        try:
            with socket.socket() as s:
                s.bind(("", port))
                return port
        except Exception:
            continue
    raise RuntimeError("No free port in range 5000-6000 found")


def run(
    host: str = "0.0.0.0",
    port: Optional[int] = None,
    mount_path: str = "/",
    streamable_http_path: str = "/mcp",
    transport: Literal["stdio", "sse", "streamable-http"] = "streamable-http",
    disable_web_search_tools: bool = False,
    disable_llm_tools: bool = False,
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
    server.add_tool(compile_latex_from_file)
    server.add_tool(compile_latex_from_str)
    server.add_tool(get_latex_template)
    server.add_tool(get_latex_templates_list)
    server.add_tool(visit_webpage)
    server.add_tool(download_pdf_paper)
    server.add_tool(read_pdf)

    if not disable_web_search_tools:
        if os.getenv("TAVILY_API_KEY"):
            server.add_tool(tavily_web_search)
        if os.getenv("EXA_API_KEY"):
            server.add_tool(exa_web_search)
        if os.getenv("BRAVE_API_KEY"):
            server.add_tool(brave_web_search)
        if os.getenv("EXA_API_KEY") or os.getenv("BRAVE_API_KEY") or os.getenv("TAVILY_API_KEY"):
            server.add_tool(web_search)

    if not disable_llm_tools and os.getenv("OPENROUTER_API_KEY"):
        server.add_tool(extract_bitflip_info)
        server.add_tool(generate_research_proposals)
        server.add_tool(score_research_proposals)
        server.add_tool(document_qa)
        server.add_tool(review_pdf_paper)

    if port is None:
        port = int(os.environ.get("PORT", -1))
        if port == -1:
            port = find_free_port()
    server.settings.port = port
    server.settings.host = host
    server.run(transport=transport)


if __name__ == "__main__":
    fire.Fire(run)
