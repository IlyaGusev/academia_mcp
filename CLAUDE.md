# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Academia MCP is an MCP (Model Context Protocol) server that provides tools for searching, fetching, analyzing, and reporting on scientific papers and datasets. It integrates with multiple academic APIs (ArXiv, ACL Anthology, Semantic Scholar, Hugging Face) and web search providers (Exa, Brave, Tavily), plus optional LLM-powered document analysis tools.

**Key Features:**
- ArXiv and ACL Anthology search/download
- Semantic Scholar citation graphs
- Hugging Face datasets search
- Web search and page crawling
- LaTeX compilation and PDF reading
- LLM-powered document QA and research proposal workflows

**Tech Stack:**
- Python 3.12+ with type hints (strict mypy)
- FastMCP framework for the MCP server
- OpenAI SDK for LLM calls (via OpenRouter)
- Pydantic for data models and settings
- Fire for CLI argument parsing
- Multiple transport options: stdio, SSE, streamable-http

## Development Commands

**IMPORTANT: Always prefer `make` commands when available.** The Makefile provides consistent, tested workflows.

### Setup
```bash
# Create virtual environment and install dependencies
uv venv .venv
make install
```

### Validation (ALWAYS run before committing)
```bash
# Format code with black (line length: 100)
make black

# Run all validation: black, flake8, mypy --strict
make validate
```

This is the most important command - run `make validate` frequently during development.

### Testing
```bash
# Run full test suite (via make)
make test

# Run a single test file
uv run pytest -s ./tests/test_arxiv_search.py

# Run a specific test
uv run pytest -s ./tests/test_arxiv_search.py::test_arxiv_search
```

### Running the Server Locally
```bash
# Run with streamable-http (default, port 5056)
uv run -m academia_mcp --transport streamable-http

# Run with stdio (for Claude Desktop)
uv run -m academia_mcp --transport stdio

# Run with custom port
uv run -m academia_mcp --transport streamable-http --port 8080
```

### Publishing
```bash
make publish  # Builds and publishes to PyPI
```

## Architecture

### Server Initialization (server.py)

The `create_server()` function in `academia_mcp/server.py` is the heart of the application:

1. **Core Tools** (always available): arxiv_search, arxiv_download, anthology_search, s2_* (Semantic Scholar), hf_datasets_search, visit_webpage, get_latex_templates_list, show_image, yt_transcript

2. **Conditional Tool Registration** (based on environment variables):
   - `WORKSPACE_DIR` set → enables compile_latex, download_pdf_paper, read_pdf
   - `OPENROUTER_API_KEY` set → enables LLM tools (document_qa, review_pdf_paper, bitflip tools, describe_image)
   - `EXA_API_KEY`/`BRAVE_API_KEY`/`TAVILY_API_KEY` set → enables respective web_search tools

3. **Transport Modes**:
   - `stdio`: for local MCP clients (Claude Desktop)
   - `streamable-http`: HTTP with CORS enabled for browser clients
   - `sse`: server-sent events

### Tool Structure

All tools live in `academia_mcp/tools/` and follow this pattern:
- Each tool is a standalone async function with type hints
- Tools use Pydantic models for inputs/outputs (enables structured_output mode)
- Most tools are registered with `structured_output=True` for schema validation
- Tools import from shared utilities (`utils.py`, `llm.py`, `settings.py`)

**Key Tool Categories:**
- **Search tools**: arxiv_search.py, anthology_search.py, openalex.py, s2.py, hf_datasets_search.py, web_search.py
- **Fetch/download tools**: arxiv_download.py, visit_webpage.py, review.py
- **Document processing**: latex.py (compile_latex, read_pdf), image_processing.py
- **LLM-powered tools**: document_qa.py, bitflip.py (research proposals), review.py

### Settings Management (settings.py)

Uses `pydantic-settings` to load configuration from `.env` file or environment variables:
- API keys: OPENROUTER_API_KEY, TAVILY_API_KEY, EXA_API_KEY, BRAVE_API_KEY, OPENAI_API_KEY
- Model names: REVIEW_MODEL_NAME, BITFLIP_MODEL_NAME, DOCUMENT_QA_MODEL_NAME, DESCRIBE_IMAGE_MODEL_NAME
- Workspace: WORKSPACE_DIR (Path), PORT (int)
- All settings accessible via `from academia_mcp.settings import settings`

### LLM Integration (llm.py)

Two main functions for calling LLMs via OpenRouter:
- `llm_acall()`: unstructured text response
- `llm_acall_structured()`: structured response with Pydantic validation (uses OpenAI's `.parse()` with retry logic)

Both use `ChatMessage` model for message formatting.

### Utilities (utils.py)

Common helper functions used across tools:
- `get_with_retries()`: HTTP GET with retry logic
- File handling utilities
- Text processing helpers

## Adding New Tools

To add a new tool:

1. Create a new file in `academia_mcp/tools/` (e.g., `my_tool.py`)
2. Define Pydantic models for input/output if using structured output
3. Implement an async function with proper type hints
4. Export the function in `academia_mcp/tools/__init__.py`
5. Register the tool in `create_server()` in `academia_mcp/server.py`
6. Add tests in `tests/test_my_tool.py`

Example pattern:
```python
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    query: str = Field(description="Search query")

class MyToolOutput(BaseModel):
    result: str = Field(description="Result")

async def my_tool(query: str) -> MyToolOutput:
    # Implementation
    return MyToolOutput(result="...")
```

Then in server.py:
```python
from academia_mcp.tools.my_tool import my_tool
# ...
server.add_tool(my_tool, structured_output=True)
```

## Testing Notes

- Tests use pytest with asyncio support (see `pytest.ini_options` in pyproject.toml)
- `conftest.py` contains shared fixtures
- Tests requiring API keys should check for env vars or use mocking
- Workspace-dependent tests use `tests/workdir/` for temporary files

## Code Style

- Line length: 100 characters (black)
- Strict mypy type checking
- Import sorting with isort
- All public APIs should have type hints
- Use Pydantic models for data validation

### Comments and Documentation

**DO NOT write inline comments explaining what code does.** The code should be self-explanatory through:
- Clear variable and function names
- Type hints
- Well-structured code

**ONLY write docstrings for MCP tools** (functions registered with `server.add_tool()`). These docstrings become the tool descriptions in the MCP protocol, so they must clearly explain:
- What the tool does
- What parameters it accepts
- What it returns

Example of acceptable docstring for an MCP tool:
```python
async def arxiv_search(query: str, limit: int = 10) -> ArxivSearchResponse:
    """
    Search arXiv for papers matching the query.

    Supports field-specific queries (e.g., 'ti:neural networks' for title search).
    Returns paper metadata including title, authors, abstract, and arXiv ID.
    """
    ...
```

**Do not write docstrings** for internal helper functions, utilities, or Pydantic models - type hints and clear naming are sufficient.

## Environment Variables for Testing

When testing locally, create a `.env` file in the project root:
```
OPENROUTER_API_KEY=your_key_here
WORKSPACE_DIR=/path/to/workspace
# Optional: EXA_API_KEY, BRAVE_API_KEY, TAVILY_API_KEY, OPENAI_API_KEY
```

## LaTeX/PDF Requirements

For LaTeX compilation and PDF processing:
- Install TeX Live: `sudo apt install texlive-latex-base texlive-fonts-recommended texlive-latex-extra texlive-science latexmk`
- Ensure `pdflatex` and `latexmk` are on PATH

## Docker

Pre-built image available: `phoenix120/academia_mcp`

Build locally:
```bash
docker build -t academia_mcp .
```

Run with workspace volume:
```bash
docker run --rm -p 5056:5056 \
  -e OPENROUTER_API_KEY=your_key \
  -e WORKSPACE_DIR=/workspace \
  -v "$PWD/workdir:/workspace" \
  academia_mcp
```
