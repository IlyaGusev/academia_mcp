import pytest
from pathlib import Path

from academia_mcp.settings import settings

settings.WORKSPACE_DIR = Path(__file__).parent / "workdir"


@pytest.fixture
def test_image_url() -> str:
    return "https://arxiv.org/html/2409.06820v4/extracted/6347978/pingpong_v3.drawio.png"


@pytest.fixture
def test_audio_url() -> str:
    return "https://raw.githubusercontent.com/voxserv/audio_quality_testing_samples/refs/heads/master/testaudio/16000/test01_20s.wav"
