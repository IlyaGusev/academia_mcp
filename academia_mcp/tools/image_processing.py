import asyncio
import base64
import contextlib
import json
import logging
import os
import threading
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Optional, Any

import httpx
from paddleocr import PaddleOCR  # type: ignore
from PIL import Image
from pydantic import BaseModel

from academia_mcp.files import get_workspace_dir
from academia_mcp.llm import ChatMessage, llm_acall
from academia_mcp.settings import settings

paddlex_logger = logging.getLogger("paddlex")
paddleocr_logger = logging.getLogger("paddleocr")
paddlex_logger.setLevel(logging.ERROR)
paddleocr_logger.setLevel(logging.ERROR)

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
    "text": dedent(
        """You are performing OCR and transcription.
        Extract ALL text and numbers from the image verbatim.
        - Preserve original casing, punctuation, symbols, mathematical notation, and whitespace layout when possible.
        - If layout is multi-column or tabular, reconstruct lines top-to-bottom, left-to-right; use line breaks between blocks.
        - For any uncertain or low-confidence characters, mark with a '?' and include a note.
        - After the raw extraction, provide a clean, normalized version (fixing obvious OCR artifacts) as a separate section.
        Return three sections:
        [GENERAL IMAGE DESCRIPTION]
        ...
        [RAW TRANSCRIPTION]
        ...
        [NORMALIZED TRANSCRIPTION]
        ...
        """
    ),
}


class OCRBox(BaseModel):  # type: ignore
    poly: List[List[float]]
    text: str
    score: float


class OCRSingleton:
    instance: Optional[PaddleOCR] = None
    lock: threading.Lock = threading.Lock()

    @classmethod
    def get(cls) -> PaddleOCR:
        if cls.instance is not None:
            return cls.instance
        with cls.lock:
            if cls.instance is None:
                with open(os.devnull, "w") as devnull:
                    with contextlib.redirect_stderr(devnull):
                        cls.instance = PaddleOCR(
                            use_doc_orientation_classify=False,
                            use_doc_unwarping=False,
                            use_textline_orientation=False,
                        )
        return cls.instance


async def _run_ocr(path: str) -> Dict[str, Any]:
    def _sync_ocr(path: str) -> Dict[str, Any]:
        try:
            ocr = OCRSingleton.get()
            with open(os.devnull, "w") as devnull:
                with contextlib.redirect_stderr(devnull):
                    result = ocr.predict(input=path)[0]
            rec_texts = result["rec_texts"]
            rec_scores = result["rec_scores"]
            rec_polys = result["rec_polys"]
        except Exception as e:
            return {"error": str(e)}
        items = []
        for poly, text, score in zip(rec_polys, rec_texts, rec_scores):
            items.append(OCRBox(poly=poly, text=text, score=score).model_dump())
        return {"boxes": items}

    return await asyncio.to_thread(_sync_ocr, path)


def show_image(path: str) -> Dict[str, str]:
    """
    Reads an image from the specified URL or from the current work directory.
    Always call this function at the end of the code block.
    For instance:
    ```python
    show_image("https://example.com/image.png")
    ```
    Do not print it ever, just return as the last expression.

    Args:
        path: Path to file inside current work directory or web URL
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
            - "text": Extract and describe text or numbers with an OCR pipeline.
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
            "image_url": {"url": f"data:image/png;base64,{image_base64}"},
        },
    ]
    model_name = settings.DESCRIBE_IMAGE_MODEL_NAME
    llm_kwargs = {}
    if description_type in {"text", "chess"}:
        llm_kwargs["temperature"] = 0.0
    response = await llm_acall(
        model_name=model_name,
        messages=[ChatMessage(role="user", content=content)],
        **llm_kwargs,
    )
    if description_type == "text":
        ocr_response = await _run_ocr(path)
        response = json.dumps(
            {
                "vlm_response": response,
                "ocr_response": ocr_response if ocr_response else [],
            }
        )
    return response
