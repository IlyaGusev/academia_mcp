# Academia MCP

[![PyPI](https://img.shields.io/pypi/v/academia-mcp?label=PyPI%20package)](https://pypi.org/project/academia-mcp/)
[![CI](https://github.com/IlyaGusev/academia_mcp/actions/workflows/python.yml/badge.svg)](https://github.com/IlyaGusev/academia_mcp/actions/workflows/python.yml)
[![License](https://img.shields.io/github/license/IlyaGusev/academia_mcp)](LICENSE)
[![smithery badge](https://smithery.ai/badge/@IlyaGusev/academia_mcp)](https://smithery.ai/server/@IlyaGusev/academia_mcp)
[![Verified on MseeP](https://mseep.ai/badge.svg)](https://mseep.ai/app/e818878b-c3a6-4b3d-a5b4-e54dcd1f1fed)

MCP server with tools to search, fetch, analyze, and report on scientific papers and datasets.

### Features
- ArXiv search and download
- ACL Anthology search
- Hugging Face datasets search
- Semantic Scholar citations and references
- Web search via Exa, Brave, or Tavily
- Web page crawler, LaTeX compilation, PDF reading
- Optional LLM-powered tools for document QA and research proposal workflows

### Requirements
- Python 3.12+

### Install
- Using pip (end users):
```bash
pip3 install academia-mcp
```

- For development (uv + Makefile):
```bash
uv venv .venv
make install
```

### Quickstart
- Run over HTTP (default transport):
```bash
uv run -m academia_mcp --transport streamable-http
```

- Run over stdio (for local MCP clients like Claude Desktop):
```bash
python -m academia_mcp --transport stdio
```

Notes:
- Transports: `stdio`, `sse`, `streamable-http`.
- `host`/`port` are used for HTTP transports; ignored for `stdio`. Default port is `5056` (or `PORT`).

### Claude Desktop config
```json
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

### Available tools (one-liners)
- `arxiv_search`: Query arXiv with field-specific queries and filters.
- `arxiv_download`: Fetch a paper by ID and convert to structured text (HTML/PDF modes).
- `anthology_search`: Search ACL Anthology with fielded queries and optional date filtering.
- `hf_datasets_search`: Find Hugging Face datasets with filters and sorting.
- `s2_get_citations`: List papers citing a given arXiv paper (Semantic Scholar Graph).
- `s2_get_references`: List papers referenced by a given arXiv paper.
- `visit_webpage`: Fetch and normalize a web page.
- `web_search`: Unified search wrapper; available when at least one of Exa/Brave/Tavily keys is set.
- `exa_web_search`, `brave_web_search`, `tavily_web_search`: Provider-specific search.
- `get_latex_templates_list`, `get_latex_template`: Enumerate and fetch built-in LaTeX templates.
- `compile_latex`: Compile LaTeX to PDF in `WORKSPACE_DIR`.
- `read_pdf`: Extract text per page from a PDF.
- `download_pdf_paper`, `review_pdf_paper`: Download and optionally review PDFs (requires LLM + workspace).
- `document_qa`: Answer questions over provided document chunks (requires LLM).
- `extract_bitflip_info`, `generate_research_proposals`, `score_research_proposals`: Research proposal helpers (requires LLM).

Availability notes:
- Set `WORKSPACE_DIR` to enable `compile_latex`, `read_pdf`, `download_pdf_paper`, and `review_pdf_paper`.
- Set `OPENROUTER_API_KEY` to enable LLM tools (`document_qa`, `review_pdf_paper`, and bitflip tools).
- Set one or more of `EXA_API_KEY`, `BRAVE_API_KEY`, `TAVILY_API_KEY` to enable `web_search` and provider tools.

### Environment variables
Set as needed depending on which tools you use:

- `OPENROUTER_API_KEY`: required for LLM-related tools.
- `BASE_URL`: override OpenRouter base URL.
- `DOCUMENT_QA_MODEL_NAME`: override default model for `document_qa`.
- `BITFLIP_MODEL_NAME`: override default model for bitflip tools.
- `TAVILY_API_KEY`: enables Tavily in `web_search`.
- `EXA_API_KEY`: enables Exa in `web_search` and `visit_webpage`.
- `BRAVE_API_KEY`: enables Brave in `web_search`.
- `WORKSPACE_DIR`: directory for generated files (PDFs, temp artifacts).
- `PORT`: HTTP port (default `5056`).

You can put these in a `.env` file in the project root.

### Docker
Build the image:
```bash
docker build -t academia_mcp .
```

Run the server (HTTP):
```bash
docker run --rm -p 5056:5056 \
  -e PORT=5056 \
  -e OPENROUTER_API_KEY=your_key_here \
  -e WORKSPACE_DIR=/workspace \
  -v "$PWD/workdir:/workspace" \
  academia_mcp
```

Or use existing image: `phoenix120/academia_mcp`

### Examples
- [Comprehensive report screencast (YouTube)](https://www.youtube.com/watch?v=4bweqQcN6w8)
- [Single paper screencast (YouTube)](https://www.youtube.com/watch?v=IAAPMptJ5k8)

### Makefile targets
- `make install`: install the package in editable mode with uv
- `make validate`: run black, flake8, and mypy (strict)
- `make test`: run the test suite with pytest
- `make publish`: build and publish using uv

### LaTeX/PDF requirements
Only needed for LaTeX/PDF tools. Ensure a LaTeX distribution is installed and `pdflatex` is on PATH, as well as `latexmk`. On Debian/Ubuntu:
```bash
sudo apt install texlive-latex-base texlive-fonts-recommended texlive-latex-extra texlive-science latexmk
```
