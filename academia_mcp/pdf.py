from pathlib import Path
from typing import List

from pypdf import PdfReader
from PIL import Image
import pymupdf  # type: ignore

from academia_mcp.utils import get_with_retries


def download_pdf(url: str, output_path: Path) -> None:
    response = get_with_retries(url)
    response.raise_for_status()
    content_type = response.headers.get("content-type")
    assert content_type
    assert "application/pdf" in content_type.lower()
    with open(output_path.resolve(), "wb") as fp:
        fp.write(response.content)


def parse_pdf_file(pdf_path: Path) -> List[str]:
    # Why not Marker? Because it is too heavy.
    reader = PdfReader(str(pdf_path.resolve()))

    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text()
            if not text:
                continue
            prefix = f"## Page {page_number}\n\n"
            pages.append(prefix + text)
        except Exception:
            continue
    return pages


def parse_pdf_file_to_images(pdf_path: Path) -> List[Image.Image]:
    doc = pymupdf.open(str(pdf_path.resolve()))
    images = []
    for page in doc:
        pil_image: Image.Image = page.get_pixmap().pil_image()
        images.append(pil_image)
    return images
