import pytest
from pathlib import Path

from academia_mcp.settings import settings

settings.WORKSPACE_DIR = Path(__file__).parent / "workdir"


@pytest.fixture
def test_image_url() -> str:
    return "https://arxiv.org/html/2409.06820v4/extracted/6347978/pingpong_v3.drawio.png"
