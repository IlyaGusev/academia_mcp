from .arxiv_search import arxiv_search
from .anthology_search import anthology_search
from .arxiv_download import arxiv_download
from .hf_datasets_search import hf_datasets_search
from .s2 import s2_get_references, s2_get_citations, s2_corpus_id_from_arxiv_id, s2_get_info
from .document_qa import document_qa
from .latex import (
    compile_latex,
    get_latex_template,
    get_latex_templates_list,
    read_pdf,
)
from .web_search import web_search, tavily_web_search, exa_web_search, brave_web_search
from .visit_webpage import visit_webpage
from .bitflip import extract_bitflip_info, generate_research_proposals, score_research_proposals
from .review import review_pdf_paper, download_pdf_paper, review_pdf_paper_by_url
from .show_image import show_image, describe_image
from .speech_to_text import speech_to_text

__all__ = [
    "arxiv_search",
    "arxiv_download",
    "anthology_search",
    "s2_get_references",
    "s2_get_citations",
    "s2_corpus_id_from_arxiv_id",
    "s2_get_info",
    "hf_datasets_search",
    "document_qa",
    "compile_latex",
    "get_latex_template",
    "get_latex_templates_list",
    "web_search",
    "tavily_web_search",
    "exa_web_search",
    "brave_web_search",
    "visit_webpage",
    "extract_bitflip_info",
    "generate_research_proposals",
    "score_research_proposals",
    "review_pdf_paper",
    "review_pdf_paper_by_url",
    "download_pdf_paper",
    "read_pdf",
    "show_image",
    "describe_image",
    "speech_to_text",
]
