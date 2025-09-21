import base64
from pathlib import Path
from io import BytesIO
from typing import Dict, Optional
from textwrap import dedent

import httpx
from PIL import Image

from academia_mcp.files import get_workspace_dir
from academia_mcp.settings import settings
from academia_mcp.llm import llm_acall, ChatMessage


DESCRIBE_PROMPTS = {
    "general": "Provide a general description of this image. Focus on the main subjects, colors, and overall scene.",
    "detailed": dedent(
        """Analyze this image in detail. Include:
        1. Main subjects and their relationships
        2. Colors, lighting, and composition
        3. Any text or symbols present
        4. Context or possible meaning
        5. Notable details or interesting elements"""
    ),
    "chess": dedent(
        """Analyze this chess position and provide a detailed description including:
        1. List of pieces on the board for both white and black
        2. Whose turn it is to move
        3. Basic evaluation of the position
        4. Any immediate tactical opportunities or threats
        5. Suggested next moves with brief explanations"""
    ),
    "text": "Extract and describe any text present in this image. If there are multiple pieces of text, organize them clearly.",
}


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


async def describe_image(
    path: str, description_type: str = "general", custom_prompt: Optional[str] = None
) -> str:
    """
    Tool to analyze and describe any image using GPT-4 Vision API.

    Returns a description of the image based on the requested type.

    Args:
        image_path (str): Path to the image file.
        description_type (str): Type of description to generate. Options:
            - "general": General description of the image
            - "detailed": Detailed analysis of the image
            - "chess": Analysis of a chess position
            - "text": Extract and describe text from the image
            - "custom": Custom description based on user prompt
    """
    image_base64 = show_image(path)["image_base64"]
    assert (
        description_type in DESCRIBE_PROMPTS or description_type == "custom"
    ), f"Invalid description type: {description_type}"
    prompt = DESCRIBE_PROMPTS.get(description_type, custom_prompt)
    assert prompt and prompt.strip(), "Please provide a non-empty prompt"
    content = [
        {"type": "text", "text": prompt},
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
        },
    ]
    model_name = settings.DESCRIBE_IMAGE_MODEL_NAME
    response = await llm_acall(
        model_name=model_name,
        messages=[ChatMessage(role="user", content=content)],
    )
    return response
