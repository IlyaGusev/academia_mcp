from academia_mcp.tools import visit_webpage


def test_visit_webpage_basic() -> None:
    content = visit_webpage("https://example.com/", provider="basic")
    assert content.text is not None
    assert content.id == "https://example.com/"
    assert content.provider == "basic"
    assert "Example Domain" in content.text


def test_visit_webpage_exa() -> None:
    content = visit_webpage("https://example.com/", provider="exa")
    assert content.text is not None
    assert content.id == "https://example.com/"
    assert content.provider == "exa"
    assert "Example Domain" in content.text


def test_visit_webpage_pdf() -> None:
    content = visit_webpage("https://arxiv.org/pdf/2409.06820")
    assert content.text is not None
    assert "A Benchmark for Role-Playing" in content.text


def test_visit_webpage_nature() -> None:
    url = "https://www.nature.com/nature/articles?page=51&searchType=journalSearch&sort=PubDate&type=article&year=2020"
    content = visit_webpage(url, provider="basic")
    assert content.text is not None
    assert "1002" in content.text


def test_visit_webpage_exception() -> None:
    url = "https://www.researchgate.net/profile/Peter-Giovannini"
    content = visit_webpage(url)
    assert content.error is not None
