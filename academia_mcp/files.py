from pathlib import Path

from academia_mcp.settings import settings

DIR_PATH = Path(__file__).parent
ROOT_PATH = DIR_PATH.parent
DEFAULT_LATEX_TEMPLATES_DIR_PATH: Path = DIR_PATH / "latex_templates"


def get_workspace_dir() -> Path:
    assert settings.WORKSPACE_DIR is not None, "Please set the WORKSPACE_DIR environment variable"
    directory = Path(settings.WORKSPACE_DIR)
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    return directory
