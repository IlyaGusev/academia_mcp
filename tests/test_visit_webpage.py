from academia_mcp.tools import visit_webpage


def test_visit_webpage_basic() -> None:
    content = visit_webpage("https://example.com/", provider="basic")
    assert content is not None
    assert "Example Domain" in content
    assert "illustrative" in content


def test_visit_webpage_exa() -> None:
    content = visit_webpage("https://example.com/", provider="exa")
    assert content is not None
    assert "Example Domain" in content
    assert "illustrative" in content


def test_visit_webpage_pdf() -> None:
    content = visit_webpage("https://arxiv.org/pdf/2409.06820")
    assert "A Benchmark for Role-Playing" in content


def test_visit_webpage_nature() -> None:
    url = "https://www.nature.com/nature/articles?page=51&searchType=journalSearch&sort=PubDate&type=article&year=2020"
    content = visit_webpage(url, provider="basic")
    assert "1002" in content


def test_visit_webpage_github_issue() -> None:
    url = "https://github.com/numpy/numpy/issues/10881"
    content = visit_webpage(url, provider="tavily")
    assert "on Apr 15, 2018" in str(content)


def test_visit_webpage_exception() -> None:
    url = "https://www.researchgate.net/profile/Peter-Giovannini"
    content = visit_webpage(url)
    assert "error" in str(content)
