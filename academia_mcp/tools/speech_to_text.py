from pathlib import Path
from io import BytesIO

import httpx
from openai import AsyncOpenAI
from academia_mcp.files import get_workspace_dir

from academia_mcp.settings import settings


async def speech_to_text(audio_path: str, provider: str = "openai") -> str:
    """
    Tool to convert speech to text using OpenAI's Whisper model.

    Returns transcribed text from the audio file.

    Args:
        audio_path (str): Path to the audio file.
        provider (str): Provider to use. Currently only "openai" is supported.
    """

    AVAILABLE_PROVIDERS = ("openai",)
    assert (
        provider in AVAILABLE_PROVIDERS
    ), f"Invalid provider: {provider}. Available providers: {AVAILABLE_PROVIDERS}"

    if audio_path.startswith("http"):
        response = httpx.get(audio_path, timeout=10)
        response.raise_for_status()
        ext = audio_path.split(".")[-1]
        audio_file = BytesIO(response.content)
        audio_file.name = f"audio_file.{ext}"
    else:
        full_audio_path = Path(audio_path)
        if not full_audio_path.exists():
            full_audio_path = Path(get_workspace_dir()) / audio_path
            assert full_audio_path.exists(), f"Audio file {audio_path} does not exist"
        audio_file = BytesIO(open(full_audio_path, "rb").read())
        audio_file.name = audio_path.split("/")[-1]

    assert provider == "openai"
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    result = await client.audio.transcriptions.create(
        model="gpt-4o-transcribe",
        file=audio_file,
        response_format="text",
    )
    return result
