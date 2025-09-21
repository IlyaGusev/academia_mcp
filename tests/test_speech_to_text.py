import httpx

from academia_mcp.tools import speech_to_text
from academia_mcp.files import get_workspace_dir


async def test_speech_to_text_base(test_audio_url: str) -> None:
    result = await speech_to_text(test_audio_url)
    assert result is not None
    assert "dancing in the masquerade" in str(result).lower()


async def test_speech_to_text_local(test_audio_url: str) -> None:
    response = httpx.get(test_audio_url, timeout=10)
    response.raise_for_status()
    ext = test_audio_url.split(".")[-1]
    with open(get_workspace_dir() / f"audio_file.{ext}", "wb") as fp:
        fp.write(response.content)
    result = await speech_to_text(f"audio_file.{ext}")
    assert result is not None
    assert "dancing in the masquerade" in str(result).lower()
