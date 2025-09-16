from typing import Optional
from pathlib import Path

from academia_mcp.settings import settings

DIR_PATH = Path(__file__).parent
ROOT_PATH = DIR_PATH.parent
DEFAULT_WORKSPACE_DIR_PATH: Path = DIR_PATH / "workdir"
DEFAULT_LATEX_TEMPLATES_DIR_PATH: Path = DIR_PATH / "latex_templates"


class WorkspaceDirectory:
    workspace_dir: Optional[Path] = None

    @classmethod
    def get_dir(cls) -> Path:
        if cls.workspace_dir is None:
            return Path(settings.WORKSPACE_DIR)
        return cls.workspace_dir

    @classmethod
    def set_dir(cls, workspace_dir: Path) -> None:
        cls.workspace_dir = workspace_dir


def get_workspace_dir() -> Path:
    directory = WorkspaceDirectory.get_dir()
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    return directory
