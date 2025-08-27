from academia_mcp.tools.review import review_pdf_paper, download_pdf_paper


async def test_review_pdf_paper() -> None:
    download_pdf_paper("https://arxiv.org/pdf/2502.01220")
    review = await review_pdf_paper("2502.01220.pdf")
    assert review
