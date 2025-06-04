from academia_mcp.tools import arxiv_download


def test_arxiv_download() -> None:
    result = arxiv_download("2409.06820")
    assert "pingpong" in result.lower()


def test_arxiv_download_pdf() -> None:
    result = arxiv_download("2401.12474")
    assert "ditto" in result.lower()


def test_arxiv_download_bug() -> None:
    paper = arxiv_download("2409.14913v2")
    assert "Performance improves incrementally upon frontier model releases" in paper

    paper = arxiv_download("2501.08838v1")
    assert "ToMATO" in paper

    paper = arxiv_download("2501.06964v1")
    assert "Patient-Centric" in paper

    paper = arxiv_download("2412.08389v1")
    assert "enhance the efficacy of ESC systems" in paper
