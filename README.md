# Academia MCP

[![PyPI](https://img.shields.io/pypi/v/codearkt?label=PyPI%20package)](https://pypi.org/project/academia-mcp/)
[![CI](https://github.com/IlyaGusev/academia_mcp/actions/workflows/python.yml/badge.svg)](https://github.com/IlyaGusev/academia_mcp/actions/workflows/python.yml)
[![License](https://img.shields.io/github/license/IlyaGusev/academia_mcp)](LICENSE)
[![smithery badge](https://smithery.ai/badge/@IlyaGusev/academia_mcp)](https://smithery.ai/server/@IlyaGusev/academia_mcp)

A collection of MCP tools related to the search of scientific papers:
- ArXiv search and download
- ACL Anthology search
- HuggingFact datasets search
- Semantic Scholar citation graphs
- Web search: Exa/Brave/Tavily
- Page crawler

## Install

- Using pip (end users):
```
pip3 install academia-mcp
```

- For development (uv + Makefile):
```
uv venv .venv
make install
```

## Examples
Comprehensive report screencast: https://www.youtube.com/watch?v=4bweqQcN6w8

Single paper screencast: https://www.youtube.com/watch?v=IAAPMptJ5k8


## Claude Desktop config
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

## Running the server (CLI)

```
uv run -m academia_mcp --transport streamable-http
```

Notes:
- Transports supported: `stdio`, `sse`, `streamable-http`.
- Host/port are used for HTTP transports; for `stdio` they are ignored.

## Makefile targets

- `make install`: install the package in editable mode with uv.
- `make validate`: run black, flake8, and mypy (strict).
- `make test`: run the test suite with pytest.
- `make publish`: build and publish using uv.

## Environment variables

Set as needed depending on which tools you use:

- `TAVILY_API_KEY`: enables Tavily in `web_search`.
- `EXA_API_KEY`: enables Exa in `web_search` and `visit_webpage`.
- `BRAVE_API_KEY`: enables Brave in `web_search`.
- `OPENROUTER_API_KEY`: required for `document_qa`.
- `BASE_URL`: override OpenRouter base URL for `document_qa` and bitflip tools.
- `DOCUMENT_QA_MODEL_NAME`: override default model for `document_qa`.
- `BITFLIP_MODEL_NAME`: override default model for bitflip tools.
- `WORKSPACE_DIR`: directory for generated files (PDFs, temp artifacts).

## md_to_pdf requirements

The `md_to_pdf` tool invokes `pdflatex`. Ensure a LaTeX distribution is installed and `pdflatex` is on PATH. On Debian/Ubuntu:

```
sudo apt install texlive-latex-base texlive-fonts-recommended texlive-latex-extra texlive-science
```
