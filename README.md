# Academia MCP

A collection of MCP tools related to the search of scientific papers:
- ArXiv search and download
- ACL Anthology search
- HuggingFact datasets search
- Semantic Scholar citation graphs
- Web search: Exa/Brave/Tavily
- Page crawler

Install:
```
pip3 install academia-mcp
```

Comprehensive report screencast: https://www.youtube.com/watch?v=4bweqQcN6w8

Single paper screencast: https://www.youtube.com/watch?v=IAAPMptJ5k8

Claude Desktop config:
```
{
  "mcpServers": {
    "academia": {
      "command": "python3",
      "args": [
        "-m",
        "academia_mcp",
        "--transport",
        "stdio"
      ]
    }
  }
}
```
