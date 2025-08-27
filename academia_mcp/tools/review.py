import base64
import os
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any

from academia_mcp.pdf import parse_pdf_file_to_images, parse_pdf_file
from academia_mcp.llm import llm_acall, ChatMessage
from academia_mcp.files import get_workspace_dir


PROMPT = """
You are an expert peer reviewer for top CS/ML venues (e.g., NeurIPS/ICML/ACL).
Your goal is to produce a fair, rigorous, and reproducible review that is maximally useful to authors and area chairs.
Be specific: cite paper sections/figures/tables when criticizing or praising.
Use actionable language ("Provide variance across 5 seeds on Dataset X; add leakage control Y").
Try to be as harsh as possible, but still be fair and constructive.

# Summary
Briefly summarize the paper and its contributions.
This is not the place to critique the paper; the authors should generally agree with a well-written summary.
This is also not the place to paste the abstract—please provide the summary in your own understanding after reading.

# Strengths and Weaknesses
Please provide a thorough assessment of the strengths and weaknesses of the paper.
A good mental framing for strengths and weaknesses is to think of reasons you might accept or reject the paper.
Please touch on the following dimensions:

## Quality
Is the submission technically sound?
Are claims well supported (e.g., by theoretical analysis or experimental results)?
Are the methods used appropriate?
Is this a complete piece of work or work in progress?
Are the authors careful and honest about evaluating both the strengths and weaknesses of their work?

## Clarity
Is the submission clearly written?
Is it well organized? (If not, please make constructive suggestions for improving its clarity.)
Does it adequately inform the reader? (Note that a superbly written paper provides enough information for an expert reader to reproduce its results.)

## Significance
Are the results impactful for the community?
Are others (researchers or practitioners) likely to use the ideas or build on them?
Does the submission address a difficult task in a better way than previous work?
Does it advance our understanding/knowledge on the topic in a demonstrable way?
Does it provide unique data, unique conclusions about existing data, or a unique theoretical or experimental approach?

## Originality
Does the work provide new insights, deepen understanding, or highlight important properties of existing methods?
Is it clear how this work differs from previous contributions, with relevant citations provided?
Does the work introduce novel tasks or methods that advance the field?
Does this work offer a novel combination of existing techniques, and is the reasoning behind this combination well-articulated?
As the questions above indicates, originality does not necessarily require introducing an entirely new method.
Rather, a work that provides novel insights by evaluating existing methods, or demonstrates improved efficiency, fairness, etc. is also equally valuable.

# Scores
Quality: Based on what you discussed in “Strengths and Weaknesses”, please assign the paper a numerical rating on the following scale to indicate the quality of the work.
4 = excellent
3 = good
2 = fair
1 = poor

Clarity: Based on what you discussed in “Strengths and Weaknesses”, please assign the paper a numerical rating on the following scale to indicate the clarity of the paper.
4 = excellent
3 = good
2 = fair
1 = poor

Significance: Based on what you discussed in “Strengths and Weaknesses”, please assign the paper a numerical rating on the following scale to indicate the significance of the paper.
4 = excellent
3 = good
2 = fair
1 = poor

Originality: Based on what you discussed in “Strengths and Weaknesses”, please assign the paper a numerical rating on the following scale to indicate the originality of the paper.
4 = excellent
3 = good
2 = fair
1 = poor

# Questions
Please list up and carefully describe questions and suggestions for the authors, which should focus on key points (ideally around 3–5) that are actionable with clear guidance.
Think of the things where a response from the author can change your opinion, clarify a confusion or address a limitation.
You are strongly encouraged to state the clear criteria under which your evaluation score could increase or decrease.
This can be very important for a productive rebuttal and discussion phase with the authors.

# Limitations
Have the authors adequately addressed the limitations and potential negative societal impact of their work?
If so, simply leave “yes”; if not, please include constructive suggestions for improvement.
In general, authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact.
You are encouraged to think through whether any critical points are missing and provide these as feedback for the authors.


# Overall
Please provide an "overall score" for this submission. Choices:
6: Strong Accept: Technically flawless paper with groundbreaking impact on one or more areas of AI, with exceptionally strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations.
5: Accept: Technically solid paper, with high impact on at least one sub-area of AI or moderate-to-high impact on more than one area of AI, with good-to-excellent evaluation, resources, reproducibility, and no unaddressed ethical considerations.
4: Borderline accept: Technically solid paper where reasons to accept outweigh reasons to reject, e.g., limited evaluation. Please use sparingly.
3: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly.
2: Reject: For instance, a paper with technical flaws, weak evaluation, inadequate reproducibility and incompletely addressed ethical considerations.
1: Strong Reject: For instance, a paper with well-known results or unaddressed ethical considerations

# Confidence
Please provide a "confidence score" for your assessment of this submission to indicate how confident you are in your evaluation.  Choices
5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.
4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.
3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.
2: You are willing to defend your assessment, but it is quite likely that you did not understand the central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.
1: Your assessment is an educated guess. The submission is not in your area or the submission was difficult to understand. Math/other details were not carefully checked.

# Format issues
Find problems with the paper formatting. Report them separately.

# Result
Return the result as a JSON object in the following format:
{
    "summary": "Summary of the paper",
    "strengths_and_weaknesses": {
        "quality": "Quality-related strengths and weaknesses",
        "clarity": "Clarity-related strengths and weaknesses",
        "significance": "Significance-related strengths and weaknesses",
        "originality": "Originality-related strengths and weaknesses",
    },
    "scores": {
        "quality": ...,
        "clarity": ...,
        "significance": ...,
        "originality": ...,
    },
    "questions": "Questions and suggestions for the authors",
    "limitations": "Limitations of the paper",
    "overall": ...,
    "confidence": ...,
    "format_issues": "Format issues",
}
"""


async def review_pdf(pdf_filename: str) -> str:
    """
    Review a pdf file.
    It parses the pdf file into images and then sends the images to the LLM for review.
    It can detect different issues with the paper formatting.
    It also returns a proper NeurIPS-stylereview.

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
    model_name = os.getenv("REVIEW_MODEL_NAME", "gpt-5")
    llm_response = await llm_acall(
        model_name=model_name,
        messages=[
            ChatMessage(role="user", content=content_parts),
        ],
    )
    return llm_response.strip()
