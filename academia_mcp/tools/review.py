import base64
import uuid
import tempfile
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any

from pydantic import BaseModel, Field

from academia_mcp.pdf import parse_pdf_file_to_images, parse_pdf_file, download_pdf
from academia_mcp.llm import llm_acall_structured, ChatMessage
from academia_mcp.files import get_workspace_dir
from academia_mcp.settings import settings


PROMPT = """
You are an expert peer reviewer for top CS/ML venues (e.g., NeurIPS/ICML/ACL).
Produce fair, strict, rigorous, reproducible reviews maximally useful to authors and ACs.
Be strict and punishing, but only for good reasons. Don't be afraid to reject a paper.
Be specific: cite paper sections/figures/tables when criticizing or praising.
Use actionable language ("Provide variance across 5 seeds on Dataset X; add leakage control Y").


# Summary
Summarize the paper and contributions in your own words (not the abstract).
Authors should agree with a well-written summary. No critique here.


# Strengths and Weaknesses
Please provide a thorough assessment of the strengths and weaknesses of the paper.
A good mental framing for strengths and weaknesses is to think of reasons you might accept or reject the paper.
Please touch on the following dimensions:

## Quality (Score 1-4: poor/fair/good/excellent)
Is the submission technically sound?
Are claims well supported (e.g., by theoretical analysis or experimental results)?
Are the methods used appropriate?
Is this a complete piece of work or work in progress?
Are the authors careful and honest about evaluating their work?

## Clarity (Score 1-4: poor/fair/good/excellent)
Is the submission clearly written?
Is it well organized? (If not, please make constructive suggestions for improving its clarity.)
Does it adequately inform the reader?
A superbly written paper provides enough information for an expert reader to reproduce its results.

## Significance (Score 1-4: poor/fair/good/excellent)
Are the results impactful for the community?
Are others (researchers or practitioners) likely to use the ideas or build on them?
Does the submission address a difficult task in a better way than previous work?
Does it advance our understanding/knowledge on the topic in a demonstrable way?
Does it provide unique data, unique conclusions about existing data, or a unique theoretical or experimental approach?

## Originality (Score 1-4: poor/fair/good/excellent)
Does the work provide new insights, deepen understanding, or highlight important properties of existing methods?
Is it clear how this work differs from previous contributions, with relevant citations provided?
Does the work introduce novel tasks or methods that advance the field?
Does this work offer a novel combination of existing techniques, and is the reasoning behind this combination well-articulated?
As the questions above indicates, originality does not necessarily require introducing an entirely new method.
Rather, a work that provides novel insights by evaluating existing methods, or demonstrates improved efficiency, fairness, etc. is also equally valuable.


# Scores
Try to be specific and detailed in your assessment.
Try not to set the same score for all the dimensions.
The scores for all dimensions should be independent of each other.
Scores should rely on strengths and weaknesses of the paper in each dimension.
If there are many substantial weaknesses, the score should be low.


# Questions
List 3-5 key actionable questions/suggestions.
Focus on points where author response could change your opinion or clarify confusion.
State clear criteria for your score changes.


# Limitations
Have the authors adequately addressed the limitations and potential negative societal impact of their work?
Please include constructive suggestions for improvement.
In general, authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact.
You are encouraged to think through whether any critical points are missing and provide these as feedback for the authors.


# Overall Score
6: Strong Accept - Flawless, groundbreaking impact, exceptional evaluation/reproducibility, no ethical issues
5: Accept - Solid, high impact (≥1 sub-area) or moderate-high (multiple areas), good-excellent evaluation/resources/reproducibility, no ethical issues
4: Borderline Accept - Solid, accept reasons outweigh reject (e.g., limited evaluation).
3: Borderline Reject - Solid, reject reasons outweigh accept.
2: Reject - Technical flaws, weak evaluation, inadequate reproducibility, incompletely addressed ethics
1: Strong Reject - Known results or unaddressed ethical issues

Don't be afraid to use 1, 2, 5, and 6.


# Confidence
5: Absolutely certain, very familiar with related work, checked math/details carefully
4: Confident but not certain, unlikely missed something
3: Fairly confident, possibly missed parts or unfamiliar with some work, details not carefully checked
2: Willing to defend but likely missed central parts, details not checked
1: Educated guess, not your area or hard to understand, details not checked


# Format issues
Find problems with the paper formatting. Report them separately.

# Result
Return the result as a JSON object in the following format:
{
    "summary": "...",
    "quality": {"strengths": ["..."], "weaknesses": ["..."], "reasoning": "...", "score": ...},
    "clarity": {"strengths": ["..."], "weaknesses": ["..."], "reasoning": "...", "score": ...},
    "significance": {"strengths": ["..."], "weaknesses": ["..."], "reasoning": "...", "score": ...},
    "originality": {"strengths": ["..."], "weaknesses": ["..."], "reasoning": "...", "score": ...},
    "questions": ["..."],
    "limitations": ["..."],
    "overall": {"reasoning": "...", "score": ...},
    "confidence": {"reasoning": "...", "score": ...},
    "format_issues": ["..."]
}

Always produce a correct JSON object.
"""


class AspectItem(BaseModel):  # type: ignore
    strengths: List[str] = Field(description="Strengths of the paper in a specific aspect")
    weaknesses: List[str] = Field(description="Weaknesses of the paper in a specific aspect")
    reasoning: str = Field(description="Reasoning about this aspect")
    score: int = Field(description="Score of this aspect")


class ReasoningItem(BaseModel):  # type: ignore
    reasoning: str = Field(description="Reasoning about this aspect")
    score: int = Field(description="Score of this aspect")


class ReviewResponse(BaseModel):  # type: ignore
    summary: str = Field(description="Summary of the paper")
    quality: AspectItem = Field(description="Quality of the paper")
    clarity: AspectItem = Field(description="Clarity of the paper")
    significance: AspectItem = Field(description="Significance of the paper")
    originality: AspectItem = Field(description="Originality of the paper")
    questions: List[str] = Field(description="Questions and suggestions for the authors")
    limitations: List[str] = Field(description="Limitations of the paper")
    overall: ReasoningItem = Field(description="Overall score and reasoning")
    confidence: ReasoningItem = Field(description="Confidence score and reasoning")
    format_issues: List[str] = Field(description="Format issues")


def _create_pdf_filename(pdf_url: str) -> str:
    if "arxiv.org/pdf" in pdf_url:
        pdf_filename = pdf_url.split("/")[-1]
    else:
        pdf_filename = str(uuid.uuid4())
    if not pdf_filename.endswith(".pdf"):
        pdf_filename += ".pdf"
    return pdf_filename


def download_pdf_paper(pdf_url: str) -> str:
    """
    Download a pdf file from a url to the workspace directory.

    Returns the path to the downloaded pdf file.

    Args:
        pdf_url: The url of the pdf file.
    """
    pdf_filename = _create_pdf_filename(pdf_url)
    pdf_path = Path(get_workspace_dir()) / pdf_filename
    download_pdf(pdf_url, pdf_path)
    return pdf_filename


async def review_pdf_paper(pdf_filename: str) -> ReviewResponse:
    """
    Review a pdf file with a paper.
    It parses the pdf file into images and then sends the images to the LLM for review.
    It can detect different issues with the paper formatting.
    Returns a proper NeurIPS-style review.

    Args:
        pdf_filename: The path to the pdf file.
    """
    pdf_filename_path = Path(pdf_filename)
    if not pdf_filename_path.exists():
        pdf_filename_path = Path(get_workspace_dir()) / pdf_filename

    images = parse_pdf_file_to_images(pdf_filename_path)
    text = "\n\n\n".join(parse_pdf_file(pdf_filename_path))
    content_parts: List[Dict[str, Any]] = [
        {
            "type": "text",
            "text": "Paper text:\n\n" + text,
        }
    ]
    for image in images:
        buffer_io = BytesIO()
        image.save(buffer_io, format="PNG")
        img_bytes = buffer_io.getvalue()
        image_base64 = base64.b64encode(img_bytes).decode("utf-8")
        image_content = {
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{image_base64}"},
        }
        content_parts.append(image_content)

    content_parts.append(
        {
            "type": "text",
            "text": "####\n\nInstructions:\n\n" + PROMPT,
        }
    )
    model_name = settings.REVIEW_MODEL_NAME
    messages = [
        ChatMessage(role="user", content=content_parts),
    ]
    result: ReviewResponse = await llm_acall_structured(
        model_name=model_name,
        messages=messages,
        response_format=ReviewResponse,
        max_completion_tokens=settings.REVIEW_MAX_COMPLETION_TOKENS,
        temperature=0.1,
    )
    return result


async def review_pdf_paper_by_url(pdf_url: str) -> ReviewResponse:
    """
    Review a pdf file with a paper by url.
    It downloads the pdf file and then reviews it.
    It parses the pdf file into images and then sends the images to the LLM for review.
    It can detect different issues with the paper formatting.
    Returns a proper NeurIPS-style review.

    Args:
        pdf_url: The url of the pdf file.
    """
    pdf_filename = _create_pdf_filename(pdf_url)
    with tempfile.TemporaryDirectory(prefix="temp_pdf_") as temp_dir:
        pdf_path = Path(temp_dir) / pdf_filename
        download_pdf(pdf_url, pdf_path)
        return await review_pdf_paper(str(pdf_path))
