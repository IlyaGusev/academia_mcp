import logging
import socket
from logging.config import dictConfig
from typing import Literal, Optional

import fire  # type: ignore
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from uvicorn.config import LOGGING_CONFIG as UVICORN_LOGGING_CONFIG

from academia_mcp.settings import settings
from academia_mcp.tools.anthology_search import anthology_search
from academia_mcp.tools.arxiv_download import arxiv_download
from academia_mcp.tools.arxiv_search import arxiv_search
from academia_mcp.tools.bitflip import (
    extract_bitflip_info,
    generate_research_proposals,
    score_research_proposals,
)
from academia_mcp.tools.document_qa import document_qa
from academia_mcp.tools.hf_datasets_search import hf_datasets_search
from academia_mcp.tools.image_processing import describe_image, show_image
from academia_mcp.tools.latex import (
    compile_latex,
    get_latex_template,
    get_latex_templates_list,
    read_pdf,
)
from academia_mcp.tools.review import download_pdf_paper, review_pdf_paper, review_pdf_paper_by_url
from academia_mcp.tools.s2 import s2_get_citations, s2_get_info, s2_get_references, s2_search
from academia_mcp.tools.speech_to_text import speech_to_text
from academia_mcp.tools.visit_webpage import visit_webpage
from academia_mcp.tools.web_search import (
    brave_web_search,
    exa_web_search,
    tavily_web_search,
    web_search,
)
from academia_mcp.tools.yt_transcript import yt_transcript


def configure_uvicorn_style_logging(level: int = logging.INFO) -> None:
    config = {**UVICORN_LOGGING_CONFIG}
    config["disable_existing_loggers"] = False
    config["root"] = {"handlers": ["default"], "level": logging.getLevelName(level)}
    dictConfig(config)


def find_free_port() -> int:
    for port in range(5000, 6001):
        try:
            with socket.socket() as s:
                s.bind(("", port))
                return port
        except Exception:
            continue
    raise RuntimeError("No free port in range 5000-6000 found")


def create_server(
    streamable_http_path: str = "/mcp",
    mount_path: str = "/",
    stateless_http: bool = True,
    disable_web_search_tools: bool = False,
    disable_llm_tools: bool = False,
    port: Optional[int] = None,
    host: str = "0.0.0.0",
) -> FastMCP:
    server = FastMCP(
        "Academia MCP",
        stateless_http=stateless_http,
        streamable_http_path=streamable_http_path,
        mount_path=mount_path,
    )
    logger = logging.getLogger(__name__)

    server.add_tool(arxiv_search, structured_output=True)
    server.add_tool(arxiv_download, structured_output=True)
    server.add_tool(visit_webpage, structured_output=True)
    server.add_tool(s2_get_citations, structured_output=True)
    server.add_tool(s2_get_references, structured_output=True)
    server.add_tool(s2_get_info, structured_output=True)
    server.add_tool(s2_search, structured_output=True)
    server.add_tool(hf_datasets_search, structured_output=True)
    server.add_tool(anthology_search, structured_output=True)
    server.add_tool(get_latex_templates_list, structured_output=True)
    server.add_tool(get_latex_template, structured_output=True)
    server.add_tool(show_image)
    server.add_tool(yt_transcript)

    if settings.WORKSPACE_DIR:
        server.add_tool(compile_latex)
        server.add_tool(download_pdf_paper)
        server.add_tool(read_pdf)
    else:
        logger.warning(
            "WORKSPACE_DIR is not set, compile_latex/download_pdf_paper/read_pdf will not be available!"
        )

    if not disable_web_search_tools:
        if settings.TAVILY_API_KEY:
            server.add_tool(tavily_web_search, structured_output=True)
        if settings.EXA_API_KEY:
            server.add_tool(exa_web_search, structured_output=True)
        if settings.BRAVE_API_KEY:
            server.add_tool(brave_web_search, structured_output=True)
        if settings.EXA_API_KEY or settings.BRAVE_API_KEY or settings.TAVILY_API_KEY:
            server.add_tool(web_search, structured_output=True)
        else:
            logger.warning("No web search tools keys are set, web_search will not be available!")

    if not disable_llm_tools and settings.OPENROUTER_API_KEY:
        server.add_tool(extract_bitflip_info, structured_output=True)
        server.add_tool(generate_research_proposals, structured_output=True)
        server.add_tool(score_research_proposals, structured_output=True)
        server.add_tool(document_qa)
        server.add_tool(describe_image)
        if settings.WORKSPACE_DIR:
            server.add_tool(review_pdf_paper, structured_output=True)
            server.add_tool(review_pdf_paper_by_url, structured_output=True)
    else:
        logger.warning("No OpenRouter API key is set, LLM-related tools will not be available!")

    if settings.OPENAI_API_KEY:
        server.add_tool(speech_to_text)
    else:
        logger.warning("No OpenAI API key is set, speech_to_text will not be available!")

    if port is None:
        if settings.PORT is not None:
            port = int(settings.PORT)
        else:
            port = find_free_port()

    server.settings.port = port
    server.settings.host = host
    return server


def run(
    host: str = "0.0.0.0",
    port: Optional[int] = None,
    mount_path: str = "/",
    streamable_http_path: str = "/mcp",
    transport: Literal["stdio", "sse", "streamable-http"] = "streamable-http",
    disable_web_search_tools: bool = False,
    disable_llm_tools: bool = False,
) -> None:
    configure_uvicorn_style_logging()
    server = create_server(
        streamable_http_path=streamable_http_path,
        mount_path=mount_path,
        disable_web_search_tools=disable_web_search_tools,
        disable_llm_tools=disable_llm_tools,
        port=port,
        host=host,
    )

    if transport == "streamable-http":
        # Enable CORS for browser-based clients
        app = server.streamable_http_app()
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id", "mcp-protocol-version"],
            max_age=86400,
        )
        uvicorn.run(
            app,
            host=server.settings.host,
            port=server.settings.port,
            log_level=server.settings.log_level.lower(),
        )
    else:
        server.run(transport=transport)


if __name__ == "__main__":
    fire.Fire(run)
