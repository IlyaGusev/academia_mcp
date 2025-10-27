# Based on
# https://arxiv.org/abs/2504.12976
# https://web.stanford.edu/class/cs197c/slides/02-literature-search.pdf

import json
import random
from typing import Any, Dict, List, Optional

from datasets import load_dataset  # type: ignore
from pydantic import BaseModel, Field

from academia_mcp.llm import ChatMessage, llm_acall_structured
from academia_mcp.settings import settings
from academia_mcp.tools.arxiv_download import arxiv_download
from academia_mcp.utils import encode_prompt


class ProposalDataset:
    dataset: Optional[List[Any]] = None

    @classmethod
    def get_dataset(cls) -> List[Any]:
        if cls.dataset is None:
            cls.dataset = list(load_dataset("UniverseTBD/hypogen-dr1")["train"])
        return cls.dataset


EXTRACT_PROMPT = """
You are a highly advanced research assistant.
You specialize in reading scientific papers for hypothesis generation and identifying innovative ideas.


## Example (BERT in NLP)
Before you begin, let 's revisit the Bit-Flip concept with an example (BERT in NLP):
- Bit: Traditional NLP models (RNNs, LSTMs) process text sequentially,
limiting their ability to understand long-range dependencies and fully capture bidirectional context.
- Flip: Instead, consider entire sentences at once, allowing context from both directions. This helps capture nuanced relationships among words.
- Spark: Bidirectional context for NLP.

## Framework
A Bit-Flip inverts a commonly held assumption,
questioning existing constraints or reapplying techniques to new domains/scales.
The "Bit" is the prevailing belief, and the "Flip" is the counterargument.

## Guidance for analysis
1. Bit (Technical Insight):
- Provide at least two sentences clearly stating the status quo or conventional approach.
- Highlight the limitation or problem it creates.
- Include enough detail so it is self-contained and does not rely on additional context from elsewhere.
2. Flip (Innovation):
- Provide at least two sentences describing the novel approach or perspective.
- Explain the method or technique that enables this change.
- Include enough detail so the Flip is understandable on its own.
3. Spark (Core Summary):
- A concise 4-6 word phrase capturing the core idea.

Now, consider this research abstract:
{{abstract}}

Your task:
Identify the Bit, Flip, and Spark from the abstract in a detailed manner:
- Bit: at least two sentences, with sufficient detail about the conventional approach and its limitation.
- Flip: at least two sentences, describing the new approach or perspective with enough detail to understand the main technique.
- Spark: a concise 4-6 word summary of the core idea.

Follow these rules:
- Do not cite the paper itself or its authors.
- Instead of saying "We/I introduced an idea", just say "An idea was introduced ...".

Return only the JSON object in this exact format (no extra text):
{
    "bit": "Technical limitation or conventional approach, in at least two sentences",
    "flip": "Innovative approach or solution, in at least two sentences",
    "spark": "4-6 word summary"
}
"""

SYSTEM_IMPROVEMENT_PROMPT = """
You are a brilliant rogue researcher who has just discovered a secret laboratory hidden behind a bookshelf.
This lab doesn't follow the boring rules of conventional academia: here, the wildest ideas become breakthrough innovations.

You've spent years watching researchers play it safe with incremental improvements and mind-numbing iterations.
But tonight you're ready to unleash scientific chaos.
"""

IMPROVEMENT_PROMPT = """
You've been handed a Bit: a technical limitation, constraint, or conventional approach from some stuffy research paper.
This Bit represents everything predictable and safe about current methods.
Your task: Shatter it completely.
Create a Flip: wildly unconventional improvement that would make traditional researchers choke on their coffee.
Then capture its essence in a Spark: brilliant summary that crackles with innovation.

- Go Beyond Novel: Your idea should feel like it came from a parallel universe where the laws of conventional thinking don't apply.
- Make It Automatically Verifiable: No human babysitters allowed. Your idea must prove itself through pure computational audacity.
- Be Surgically Specific: Vague hand-waving is for amateur rebels. Describe exactly how your mad science would work.
- Feasibility is the Key: Make it simple and executable. Try to make it reproducible.
- Channel Your Inner Contrarian: What would happen if you took the exact opposite approach?
What if you turned the problem inside-out, upside-down, or into a completely different dimension?

{% for example in examples %}
## Example {{loop.index}} of boring research
- Bit: {{example["bit"]}}
- Chain of reasoning: {{example["chain_of_reasoning"]}}
- Flip: {{example["flip"]}}
- Spark: {{example["spark"]}}
{% endfor %}

Those examples are boring, your ideas should not be like that.

Now, please propose a chain of reasoning that leads to an improvement idea for this Bit:
{{bit}}

{% if additional_context %}Additional context:
{{additional_context}}{% endif %}

Finalize your idea by providing the idea details:
- Abstract: An abstract that summarizes the proposal in conference format (approximately 250 words).
- Experiments: A list of experiments that would be conducted to validate the proposal.
Ensure these are simple and feasible. Be specific in exactly how you would test the hypothesis, and detail precise algorithmic changes.
Include the evaluation metrics you would use.
- Risks and limitations: A list of potential risks and limitations of the proposal.

Generate {{num_proposals}} proposals.

Return only the JSON list of proposals in this exact format:
{
    "proposals": [
        {
            "chain_of_reasoning": "Chain of reasoning that leads to an improvement idea for this Bit. At least 5 sentences.",
            "flip": "Your wildest, craziest, most innovative idea, in at least two sentences",
            "spark": "4-6 word summary",
            "abstract": "An abstract that summarizes the proposal in conference format (approximately 250 words).",
            "experiments": ["...", "..."],
            "risks_and_limitations": ["...", "..."]
        },
        ...
    ]
}
"""


SCORE_PROMPT = """
You are a highly advanced research assistant.
You are given a list of research proposals.
Your task is to score the proposals.

Proposals:
{% for proposal in proposals %}
----
{{proposal}}
----
{% endfor %}

Here are the criteria:
- "Strengths": A list of strengths of the proposal.
- "Weaknesses": A list of weaknesses of the proposal.
- "Novelty": Is the proposal novel? A rating from 1 to 4 (low, medium, high, very high).
- "Clarity": Is the proposal clear? A rating from 1 to 4 (low, medium, high, very high).
- "Significance": Is the proposal significant? A rating from 1 to 4 (low, medium, high, very high).
- "Feasibility": Is the proposal feasible and easy to implement? A rating from 1 to 4 (low, medium, high, very high).
- "Soundness": Is the proposal sound? A rating from 1 to 4 (poor, fair, good, excellent).
- "Overall": A rating from 1 to 10 (very strong reject to award quality).

Return only scores for all proposals in this exact format (no extra text):
{
    "proposals": [
        {
            "proposal_id": 0,
            "spark": "...",
            "strengths": ["...", "..."],
            "weaknesses": ["...", "..."],
            "novelty": 2,
            "clarity": 2,
            "significance": 2,
            "feasibility": 2,
            "soundness": 2,
            "overall": 5
        },
        ...
    ]
}
"""


class BitFlipInfo(BaseModel):  # type: ignore
    bit: str = Field(description="Technical limitation or conventional approach")
    flip: str = Field(description="Innovative approach or solution")
    spark: str = Field(description="4-6 word summary")


async def extract_bitflip_info(arxiv_id: str) -> BitFlipInfo:
    """
    Extracts the Bit-Flip information from the arXiv paper.

    A Bit-Flip is a technique that inverts a commonly held assumption,
    questioning existing constraints or reapplying techniques to new domains/scales.
    The "Bit" is the prevailing belief, and the "Flip" is the counterargument.

    Args:
        arxiv_id: The arXiv ID of the paper to extract the Bit-Flip information from.
    """
    model_name = settings.BITFLIP_MODEL_NAME
    paper = arxiv_download(arxiv_id)
    abstract = paper.abstract
    prompt = encode_prompt(EXTRACT_PROMPT, abstract=abstract)
    bitflip_info: BitFlipInfo = await llm_acall_structured(
        model_name=model_name,
        messages=[ChatMessage(role="user", content=prompt)],
        temperature=0.0,
        response_format=BitFlipInfo,
    )
    return bitflip_info


class ResearchProposal(BaseModel):  # type: ignore
    proposal_id: int = Field(default=0, description="ID of the proposal")
    flip: str = Field(description="Innovative approach or solution, in at least two sentences")
    spark: str = Field(description="4-6 word summary")
    abstract: str = Field(
        description="An abstract that summarizes the proposal in conference format."
    )
    experiments: List[str] = Field(
        description="A list of experiments that would be conducted to validate the proposal."
    )
    risks_and_limitations: List[str] = Field(
        description="A list of potential risks and limitations of the proposal."
    )


class GenerateResearchProposalResponse(BaseModel):  # type: ignore
    proposals: List[ResearchProposal] = Field(description="A list of research proposals")


async def generate_research_proposals(
    bit: str, num_proposals: int = 3, additional_context: str = ""
) -> GenerateResearchProposalResponse:
    """
    Proposes improvement ideas for the Bit.

    Args:
        bit: The Bit to propose improvement ideas for. The bit is a technical limitation or conventional approach of some paper.
        num_proposals: The number of proposals to generate.
        additional_context: Additional context to use when proposing the improvement idea.
    """
    model_name = settings.BITFLIP_MODEL_NAME
    max_completion_tokens = int(settings.BITFLIP_MAX_COMPLETION_TOKENS)
    examples = ProposalDataset.get_dataset()[:]
    examples = random.choices(examples, k=2)

    prompt = encode_prompt(
        IMPROVEMENT_PROMPT,
        bit=bit,
        examples=examples,
        num_proposals=num_proposals,
        additional_context=additional_context,
    )
    result: GenerateResearchProposalResponse = await llm_acall_structured(
        model_name=model_name,
        messages=[
            ChatMessage(role="system", content=SYSTEM_IMPROVEMENT_PROMPT),
            ChatMessage(role="user", content=prompt),
        ],
        response_format=GenerateResearchProposalResponse,
        max_completion_tokens=max_completion_tokens,
        temperature=1.0,
    )
    return result


class ScoredProposal(BaseModel):  # type: ignore
    proposal_id: int = Field(default=0, description="ID of the proposal")
    spark: str = Field(description="4-6 word summary")
    strengths: List[str] = Field(description="A list of strengths of the proposal")
    weaknesses: List[str] = Field(description="A list of weaknesses of the proposal")
    novelty: int = Field(description="Novelty rating from 1 to 4")
    clarity: int = Field(description="Clarity rating from 1 to 4")
    significance: int = Field(description="Significance rating from 1 to 4")
    feasibility: int = Field(description="Feasibility rating from 1 to 4")
    soundness: int = Field(description="Soundness rating from 1 to 4")
    overall: int = Field(description="Overall rating from 1 to 10")


class ScoreResearchProposalsResponse(BaseModel):  # type: ignore
    proposals: List[ScoredProposal] = Field(description="List of scored proposals")


async def score_research_proposals(
    proposals: str | List[Dict[str, Any]] | List[Any] | List[str] | List[ResearchProposal],
) -> ScoreResearchProposalsResponse:
    """
    Scores a list of research proposals.
    Use proposals obtained with the `generate_research_proposal` tool.

    Args:
        proposals: A list of JSON strings with research proposals.
    """
    model_name = settings.BITFLIP_MODEL_NAME
    if isinstance(proposals, str):
        proposals = json.loads(proposals)
    if isinstance(proposals, list) and proposals:
        proposals = [str(p) for p in proposals]
    assert isinstance(proposals, list), "Proposals should be a list"
    prompt = encode_prompt(SCORE_PROMPT, proposals=proposals)
    result: ScoreResearchProposalsResponse = await llm_acall_structured(
        model_name=model_name,
        messages=[ChatMessage(role="user", content=prompt)],
        response_format=ScoreResearchProposalsResponse,
        temperature=0.0,
    )
    return result
