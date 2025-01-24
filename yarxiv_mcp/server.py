import asyncio
from typing import List

from mcp.server import Server
import mcp.types as types
from mcp.server.stdio import stdio_server
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.tools import Tool

from .tools.arxiv_search import arxiv_search

server = FastMCP("My App")
server.add_tool(arxiv_search)


if __name__ == "__main__":
    server.run()
