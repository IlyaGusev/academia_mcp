import base64
from pathlib import Path
from io import BytesIO
from typing import Dict

import httpx
from PIL import Image

from academia_mcp.files import get_workspace_dir
from academia_mcp.settings import settings


def show_image(path: str) -> Dict[str, str]:
    """
    Reads an image from the specified URL or from the current work directory.
    Always call this function at the end of the code block.
    For instance:
    ```python
    show_image("https://example.com/image.png")
    ```
    Do not print it ever, just return as the last expression.

    Returns an dictionary with a single "image" key.
    Args:
        url: Path to file inside current work directory or web URL
    """
    if path.startswith("http"):
        response = httpx.get(path, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
    else:
        assert settings.WORKSPACE_DIR is not None, "WORKSPACE_DIR is not set"
        full_path = Path(path)
        if not full_path.exists():
            full_path = Path(get_workspace_dir()) / path
            assert full_path.exists(), f"Image file {path} does not exist"
        image = Image.open(str(full_path))
    buffer_io = BytesIO()
    image.save(buffer_io, format="PNG")
    img_bytes = buffer_io.getvalue()
    return {"image_base64": base64.b64encode(img_bytes).decode("utf-8")}
