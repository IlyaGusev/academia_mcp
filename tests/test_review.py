from academia_mcp.tools.review import review_pdf_paper_by_url


async def test_review_pdf_paper_by_url() -> None:
    review = await review_pdf_paper_by_url("https://arxiv.org/pdf/2502.01220")
    assert review
    assert review.format_issues
