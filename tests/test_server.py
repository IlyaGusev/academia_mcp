from typing import Dict, Any

from mcp import ClientSession
from mcp.types import CallToolResult
from mcp.client.streamable_http import streamablehttp_client

from tests.conftest import MCPServerTest


async def call_tool(mcp_server_test: MCPServerTest, tool: str, kwargs: Dict[str, Any]) -> Any:
    url = f"http://{mcp_server_test.host}:{mcp_server_test.port}/mcp"
    async with streamablehttp_client(
        url,
        timeout=60,
        sse_read_timeout=60,
    ) as (
        read_stream,
        write_stream,
        _,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result: CallToolResult = await session.call_tool(tool, kwargs)
            return result.structuredContent


def test_server_run(mcp_server_test: MCPServerTest) -> None:
    assert mcp_server_test.server is not None
    assert mcp_server_test.is_running()


async def test_server_arxiv_search(mcp_server_test: MCPServerTest) -> None:
    query = 'ti:"PingPong: A Benchmark for Role-Playing Language Models"'
    result = await call_tool(mcp_server_test, "arxiv_search", {"query": query})
    assert result["results"][0]["authors"] == "Ilya Gusev"
