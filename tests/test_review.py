from academia_mcp.tools.review import review_pdf_paper, download_pdf_paper, review_pdf_paper_by_url


async def test_review_pdf_paper() -> None:
    download_pdf_paper("https://arxiv.org/pdf/2502.01220")
    review = await review_pdf_paper("2502.01220.pdf")
    assert review


async def test_review_pdf_paper_by_url() -> None:
    review = await review_pdf_paper_by_url("https://arxiv.org/pdf/2502.01220")
    assert review
    assert "format_issues" in str(review)
