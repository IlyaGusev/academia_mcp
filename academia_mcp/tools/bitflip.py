# https://arxiv.org/abs/2504.12976
# https://web.stanford.edu/class/cs197c/slides/02-literature-search.pdf

import json
import os
import random
from typing import List, Dict, Any

from openai import OpenAI
from pydantic import BaseModel
from openai.types.chat import ChatCompletionMessage
from datasets import load_dataset  # type: ignore

from academia_mcp.tools.arxiv_download import arxiv_download
from academia_mcp.utils import extract_json, encode_prompt


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

IMPROVEMENT_PROMPT = """
You are a highly advanced research assistant.
You specialize in hypothesis generation and identifying innovative ideas.

You are given a Bit, which is a technical limitation or conventional approach of some paper.
Your task is to propose an improvement idea for the Bit called Flip and summarize it in a Spark.
Do not propose any human annotations or human-in-the-loop, the idea should be automatically verifiable.
Try to be as specific as possible.

{% for example in examples %}
## Example {{loop.index}}
- Bit: {{example["bit"]}}
- Chain of reasoning: {{example["chain_of_reasoning"]}}
- Flip: {{example["flip"]}}
- Spark: {{example["spark"]}}
{% endfor %}

Now, please propose a chain of reasoning that leads to an improvement idea for this Bit:
{{bit}}

Return only the JSON object in this exact format (no extra text):
{
    "chain_of_reasoning": "Chain of reasoning that leads to an improvement idea for this Bit. At least 5 sentences.",
    "flip": "Innovative approach or solution, in at least two sentences",
    "spark": "4-6 word summary"
}
"""


class ChatMessage(BaseModel):  # type: ignore
    role: str
    content: str | List[Dict[str, Any]]


ChatMessages = List[ChatMessage]


def extract_bitflip_info(arxiv_id: str) -> str:
    """
    Extracts the Bit-Flip information from the arXiv paper.

    A Bit-Flip is a technique that inverts a commonly held assumption,
    questioning existing constraints or reapplying techniques to new domains/scales.
    The "Bit" is the prevailing belief, and the "Flip" is the counterargument.

    Returns a JSON object in this format:
    {
        "bit": "Technical limitation or conventional approach, in at least two sentences",
        "flip": "Innovative approach or solution, in at least two sentences",
        "spark": "4-6 word summary of the core idea"
    }
    Use `json.loads` to deserialize the result if you want to get specific fields.

    Args:
        arxiv_id: The arXiv ID of the paper to extract the Bit-Flip information from.
    """
    base_url = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
    key = os.getenv("OPENROUTER_API_KEY", "")
    assert key, "Please set OPENROUTER_API_KEY in the environment variables"
    model_name = os.getenv("BITFLIP_MODEL_NAME", "deepseek/deepseek-chat-v3-0324")

    paper = arxiv_download(arxiv_id)
    abstract = json.loads(paper)["abstract"]
    prompt = encode_prompt(EXTRACT_PROMPT, abstract=abstract)
    messages: ChatMessages = [
        ChatMessage(role="user", content=prompt),
    ]
    client = OpenAI(base_url=base_url, api_key=key)
    response: ChatCompletionMessage = (
        client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.0,
        )
        .choices[0]
        .message
    )
    assert response.content, "Response content is None"
    result = extract_json(response.content)
    return json.dumps(result, ensure_ascii=False)


def propose_improvement_idea(arxiv_id: str) -> str:
    """
    Proposes an improvement idea for the arXiv paper.

    Returns a JSON object in this format:
    {
        "chain_of_reasoning": "Chain of reasoning that leads to an improvement idea.",
        "flip": "Innovative approach or solution",
        "spark": "4-6 word summary"
    }
    Use `json.loads` to deserialize the result if you want to get specific fields.

    Args:
        arxiv_id: The arXiv ID of the paper to propose an improvement idea for.
    """
    base_url = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
    key = os.getenv("OPENROUTER_API_KEY", "")
    assert key, "Please set OPENROUTER_API_KEY in the environment variables"
    model_name = os.getenv("BITFLIP_MODEL_NAME", "deepseek/deepseek-chat-v3-0324")

    bitflip_info = json.loads(extract_bitflip_info(arxiv_id))
    bit = bitflip_info["bit"]

    examples = list(load_dataset("UniverseTBD/hypogen-dr1")["train"])
    random.shuffle(examples)
    examples = examples[:4]

    prompt = encode_prompt(IMPROVEMENT_PROMPT, bit=bit, examples=examples)
    messages: ChatMessages = [
        ChatMessage(role="user", content=prompt),
    ]
    client = OpenAI(base_url=base_url, api_key=key)
    response: ChatCompletionMessage = (
        client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.0,
        )
        .choices[0]
        .message
    )
    assert response.content, "Response content is None"
    result = extract_json(response.content)
    return json.dumps(result, ensure_ascii=False)
