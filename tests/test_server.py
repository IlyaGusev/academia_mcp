from typing import Dict, Any, List

from mcp import ClientSession, Tool
from mcp.types import CallToolResult
from mcp.client.streamable_http import streamablehttp_client

from tests.conftest import MCPServerTest


async def call_tool(mcp_server_test: MCPServerTest, tool: str, kwargs: Dict[str, Any]) -> Any:
    url = f"http://{mcp_server_test.host}:{mcp_server_test.port}/mcp"
    async with streamablehttp_client(url) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result: CallToolResult = await session.call_tool(tool, kwargs)
            return result.structuredContent


async def fetch_tools(mcp_server_test: MCPServerTest) -> List[Tool]:
    url = f"http://{mcp_server_test.host}:{mcp_server_test.port}/mcp"
    all_tools: List[Tool] = []
    async with streamablehttp_client(url) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools_response = await session.list_tools()
            all_tools.extend(tools_response.tools)
    return all_tools


def test_server_run(mcp_server_test: MCPServerTest) -> None:
    assert mcp_server_test.server is not None
    assert mcp_server_test.is_running()


async def test_server_arxiv_search(mcp_server_test: MCPServerTest) -> None:
    query = 'ti:"PingPong: A Benchmark for Role-Playing Language Models"'
    result = await call_tool(mcp_server_test, "arxiv_search", {"query": query})
    assert result["results"][0]["authors"] == "Ilya Gusev"


async def test_server_tools_schemas(mcp_server_test: MCPServerTest) -> None:
    tools = {tool.name: tool for tool in await fetch_tools(mcp_server_test)}

    tool = tools["arxiv_search"]
    assert tool.outputSchema is not None
    assert "Number of results returned" in str(tool.outputSchema)
    tool = tools["arxiv_download"]
    assert tool.outputSchema is not None
    assert "Parsed references from the paper" in str(tool.outputSchema)
    tool = tools["visit_webpage"]
    assert tool.outputSchema is not None
    assert "Text content of the webpage" in str(tool.outputSchema)
    tool = tools["web_search"]
    assert tool.outputSchema is not None
    assert "Results of the search" in str(tool.outputSchema)
    tool = tools["s2_get_citations"]
    assert tool.outputSchema is not None
    assert "External IDs of the paper" in str(tool.outputSchema)
    tool = tools["s2_get_references"]
    assert tool.outputSchema is not None
    assert "External IDs of the paper" in str(tool.outputSchema)
    tool = tools["s2_get_info"]
    assert tool.outputSchema is not None
    assert "External IDs of the paper" in str(tool.outputSchema)
    tool = tools["extract_bitflip_info"]
    assert tool.outputSchema is not None
    assert "Innovative approach or solution" in str(tool.outputSchema)
    tool = tools["generate_research_proposals"]
    assert tool.outputSchema is not None
    assert "Innovative approach or solution" in str(tool.outputSchema)
    tool = tools["score_research_proposals"]
    assert tool.outputSchema is not None
    assert "ID of the proposal" in str(tool.outputSchema)
