from io import BytesIO

import httpx
from PIL import Image

from academia_mcp.tools import show_image, describe_image
from academia_mcp.files import get_workspace_dir


def test_show_image_base(test_image_url: str) -> None:
    result = show_image(test_image_url)
    assert result is not None
    assert "image_base64" in result
    assert result["image_base64"] is not None


def test_show_image_local(test_image_url: str) -> None:
    response = httpx.get(test_image_url, timeout=10)
    response.raise_for_status()
    image = Image.open(BytesIO(response.content))
    image.save(get_workspace_dir() / "test_image.png")
    result = show_image("test_image.png")
    assert result is not None
    assert "image_base64" in result
    assert result["image_base64"] is not None


async def test_describe_image_base(test_image_url: str) -> None:
    result = await describe_image(test_image_url)
    assert result is not None
    assert "Interrogator" in result
