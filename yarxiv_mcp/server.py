from mcp.server.fastmcp import FastMCP

from .tools.arxiv_search import arxiv_search

server = FastMCP("Yet Another ArXiv MCP")
server.add_tool(arxiv_search)


if __name__ == "__main__":
    server.run()
