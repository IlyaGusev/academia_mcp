# Based on
# https://github.com/SamuelSchmidgall/AgentLaboratory/blob/main/tools.py
# https://github.com/bytedance/pasa/blob/main/utils.py

import re
import json
import tempfile
from pathlib import Path
from typing import Any, List, Optional, Dict
from dataclasses import dataclass, field

import requests
import bs4
from markdownify import MarkdownConverter  # type: ignore

from academia_mcp.utils import get_with_retries
from academia_mcp.pdf import parse_pdf_file, download_pdf


HTML_URL = "https://arxiv.org/html/{paper_id}"
ABS_URL = "https://arxiv.org/abs/{paper_id}"
PDF_URL = "https://arxiv.org/pdf/{paper_id}"
SECTION_STOP_WORDS = (
    "references",
    "acknowledgments",
    "about this document",
    "appendix",
)


@dataclass
class TOCEntry:
    level: int
    title: str
    html_id: Optional[str] = None
    subsections: List["TOCEntry"] = field(default_factory=list)

    def linearize(self) -> List["TOCEntry"]:
        entries = [self]
        for subsection in self.subsections:
            entries.extend(subsection.linearize())
        return entries

    def is_excluded(self) -> bool:
        return any(ss in self.title.lower() for ss in SECTION_STOP_WORDS)

    def to_str(self) -> str:
        final_items = []
        output_index = 0
        for entry in self.linearize():
            if entry.level <= 1:
                continue
            prefix = "  " * (entry.level - 2)
            suffix = ""
            if entry.level == 2 and not entry.is_excluded():
                suffix = f" (index in 'sections': {output_index})"
                output_index += 1
            final_items.append(prefix + entry.title + suffix)
        return "\n".join(final_items)


class ArxivHTMLConverter(MarkdownConverter):  # type: ignore
    def __init__(self, base_url: str, *args: Any, **kwargs: Any) -> None:
        self.base_url = base_url

        super().__init__(*args, **kwargs)

    def convert_cite(self, el: bs4.element.Tag, text: str, convert_as_inline: bool = False) -> str:
        citations = text.split(";")
        citations = [c.strip() for c in citations if c.strip()]
        fixed_citations = []
        for citation in citations:
            fixed_citation = citation
            parts = citation.split()
            year = parts[-1]
            if len(year) > 4 and year[0] == "(" and year[-1] == ")":
                fixed_citation = f'{" ".join(parts[:-1])}, {year[1:-1]}'
            fixed_citations.append(fixed_citation)
        return f'({"; ".join(fixed_citations)})'

    def convert_sup(self, *args: Any, **kwargs: Any) -> str:
        return ""

    def convert_span(self, el: bs4.element.Tag, text: str, convert_as_inline: bool = False) -> str:
        if "class" not in el:
            return text
        if "ltx_tag_item" in el["class"]:
            return ""
        if "ltx_note_outer" in el["class"]:
            return f" (Footnote {text})"
        if "ltx_tag_note" in el["class"]:
            return text + ": "
        return text

    def convert_figure(
        self, el: bs4.element.Tag, text: str, convert_as_inline: bool = False
    ) -> str:
        if el.img:
            link = el.img.get("src")
            caption = "Figure"
            if el.figcaption:
                caption = el.figcaption.text
            return f"\n\n![{caption}]({self.base_url}/{link})\n\n"
        elif el.table:
            caption = "Table"
            if el.figcaption:
                caption = el.figcaption.text
            table_text = self.process_tag(el.table, convert_as_inline=False)
            return f"\n\n{caption}\n\n{table_text}\n\n"
        return text


def _generate_toc(soup: bs4.element.Tag) -> TOCEntry:
    stack = [TOCEntry(level=0, title="ROOT", html_id=None)]
    heading_tags = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5}
    for tag in soup.find_all(heading_tags.keys()):
        level = heading_tags[tag.name]
        while stack[-1].level >= level:
            stack.pop()
        parent_entry = stack[-1]
        section = tag.find_parent("section", id=True)
        if not section:
            continue
        section_id = section.get("id")
        assert section_id is not None
        title = tag.get_text().strip()
        new_entry = TOCEntry(level=level, title=title, html_id=section_id)
        parent_entry.subsections.append(new_entry)
        stack.append(new_entry)
    return stack[0]


def _convert_soup_to_md(soup: bs4.element.Tag, url: str) -> str:
    converter = ArxivHTMLConverter(base_url=url, strip=["div", "a"], heading_style="ATX")
    md_content: str = converter.convert_soup(soup)
    md_content = md_content.replace("\xa0", " ")
    md_content = "\n".join([line.strip() for line in md_content.split("\n")])
    lines = [line.strip() for line in md_content.split("\n\n") if line.strip()]
    md_content = "\n\n".join(lines)
    return md_content


def _build_by_toc(toc: TOCEntry, soup: bs4.element.Tag, url: str) -> List[str]:
    final_sections = []
    for toc_entry in toc.linearize():
        if toc_entry.level == 2 and not toc_entry.is_excluded():
            section = soup.find(id=toc_entry.html_id)
            assert isinstance(section, bs4.element.Tag)
            text = _convert_soup_to_md(section, url)
            final_sections.append(text)
    return final_sections


def _format_authors(authors: str) -> str:
    if not authors:
        return ""
    names = authors.split(",")
    names = [n.strip() for n in names if n.strip()]
    result = ", ".join(names[:3])
    if len(names) > 3:
        result += f", and {len(names) - 3} more authors"
    return result


def _parse_citation_metadata(metas: List[str]) -> Dict[str, Any]:
    metas = [item.replace("\n", " ") for item in metas]
    meta_string = " ".join(metas)
    authors, title, journal, year = "", "", "", None
    if len(metas) == 3:
        authors, title, journal = metas
    else:
        meta_string = re.sub(r"\.\s\d{4}[a-z]?\.", ".", meta_string)
        match = re.match(r"^(.*?\.\s)(.*?)(\.\s.*|$)", meta_string, re.DOTALL)
        if match:
            authors = match.group(1).strip() if match.group(1) else ""
            title = match.group(2).strip() if match.group(2) else ""
            journal = match.group(3).strip() if match.group(3) else ""
            if journal.startswith(". "):
                journal = journal[2:]

    if authors:
        parts = authors.strip(".").split(".")
        if parts and parts[-1].strip().isdigit():
            year = int(parts[-1].strip())
            authors = ".".join(parts[:-1])
        authors = _format_authors(authors)

    result = {
        "authors": authors,
        "year": year,
        "title": title,
        "journal": journal,
    }
    if not authors or not title:
        result["meta"] = meta_string
    return result


def _extract_citations(soup_biblist: bs4.element.Tag) -> List[Dict[str, Any]]:
    extracted = []
    for li in soup_biblist.find_all("li", recursive=False):
        metas = [x.text.strip() for x in li.find_all("span", class_="ltx_bibblock")]
        extracted.append(_parse_citation_metadata(metas))
    return extracted


def _parse_html(paper_id: str) -> Dict[str, Any]:
    url = HTML_URL.format(paper_id=paper_id)
    response = get_with_retries(url)
    response.raise_for_status()
    content = response.text

    soup = bs4.BeautifulSoup(content, features="lxml")
    article = soup.article
    assert article and isinstance(article, bs4.element.Tag)

    citations = []
    biblist_tag = article.find(class_="ltx_biblist")
    if biblist_tag and isinstance(biblist_tag, bs4.element.Tag):
        citations = _extract_citations(biblist_tag)

    toc = _generate_toc(article)
    sections = _build_by_toc(toc, article, url)
    return {
        "toc": toc.to_str(),
        "sections": sections,
        "citations": citations,
        "original_format": "html",
    }


def _parse_abs(paper_id: str) -> Dict[str, str]:
    url = ABS_URL.format(paper_id=paper_id)
    response = get_with_retries(url)
    response.raise_for_status()
    content = response.text

    soup = bs4.BeautifulSoup(content, features="lxml")
    title_tag = soup.find(class_="title")
    assert title_tag and isinstance(title_tag, bs4.element.Tag)
    title = title_tag.get_text().strip()
    title = title.replace("Title:", "")
    abstract_tag = soup.find(class_="abstract")
    assert abstract_tag and isinstance(abstract_tag, bs4.element.Tag)
    abstract = abstract_tag.get_text().strip()
    abstract = abstract.replace("Abstract:", "")
    return {"title": title, "abstract": abstract}


def _parse_pdf(paper_id: str) -> Dict[str, Any]:
    url = PDF_URL.format(paper_id=paper_id)
    with tempfile.NamedTemporaryFile(mode="w", delete=True) as temp_file:
        download_pdf(url, Path(temp_file.name))
        pages: List[str] = parse_pdf_file(Path(temp_file.name))
    return {
        "toc": "\n".join([f"Page {page_number}" for page_number in range(1, len(pages) + 1)]),
        "sections": pages,
        "citations": [],
        "original_format": "pdf",
    }


def arxiv_download(
    paper_id: str,
    include_citations: Optional[bool] = False,
    mode: Optional[str] = "html",
) -> str:
    """
    Downloads a paper from Arxiv and converts it to text.
    Use mode = "html" by default.
    Fall back to mode = "pdf" if there are any problems with the HTML version.

    Returns a JSON with a following structure:
    {
        "title": "...",
        "abstract": "...",
        "toc": "...",
        "sections": ["...", ...],
        "citations": [...]
    }
    Use `json.loads` to deserialize the result if you want to get specific fields.
    For example, `abstract = json.loads(arxiv_download("2409.06820v1"))`
    The "toc" key contains Table of Contents, that sometimes has indexing for sections.

    Args:
        paper_id: ID of the paper on Arxiv. For instance: 2409.06820v1
        include_citations: include "citations" in the result or not. False by default.
        mode: Which version of paper to use. Options: ["html", "pdf"]. "html" by default.
    """

    abs_meta = _parse_abs(paper_id)
    if mode == "html":
        try:
            content = _parse_html(paper_id)
        except requests.exceptions.HTTPError:
            content = _parse_pdf(paper_id)
    else:
        content = _parse_pdf(paper_id)

    if not include_citations and "citations" in content:
        content.pop("citations")

    return json.dumps({**abs_meta, **content}, ensure_ascii=False)
