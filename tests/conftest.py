from pathlib import Path

from academia_mcp.settings import settings

settings.WORKSPACE_DIR = Path(__file__).parent / "workdir"
