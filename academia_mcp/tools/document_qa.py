import json
from typing import List, Any, Dict

from pydantic import BaseModel

from academia_mcp.llm import llm_acall
from academia_mcp.utils import truncate_content
from academia_mcp.settings import settings


PROMPT = """You are a helpful assistant that answers questions about documents accurately and concisely.
Please answer the following questions based solely on the provided document.
If there is no answer in the document, output "There is no answer in the provided document".
First cite ALL relevant document fragments, then provide a final answer.
Answer all given questions one by one.
Make sure that you answer the actual questions, and not some other similar questions.

Questions:
{question}

Document:
==== BEGIN DOCUMENT ====
{document}
==== END DOCUMENT ====

Questions (repeated):
{question}

Your citations and answers:"""


class ChatMessage(BaseModel):  # type: ignore
    role: str
    content: str | List[Dict[str, Any]]


ChatMessages = List[ChatMessage]


async def document_qa(
    document: str | Dict[str, Any],
    question: str,
) -> str:
    """
    Answer a question about a document.
    Use this tool when you need to find relevant information in a big document.
    It takes a question and a document as inputs and generates an answer based on the document.

    Example:
    >>> document = "The quick brown fox jumps over the lazy dog."
    >>> answer = document_qa(question="What animal is mentioned? How many of them?", document=document)
    >>> print(answer)
    "The document mentions two animals: a fox and a dog. 2 animals."

    Returns an answer to all questions based on the document content.

    Args:
        question: Question (or questions) to be answered about the document.
        document: The full text of the document to analyze.
    """
    assert question and question.strip(), "Please provide non-empty 'question'"
    if isinstance(document, dict):
        document = json.dumps(document)
    assert document and document.strip(), "Please provide non-empty 'document'"

    question = truncate_content(question, settings.DOCUMENT_QA_QUESTION_MAX_LENGTH)
    document = truncate_content(document, settings.DOCUMENT_QA_DOCUMENT_MAX_LENGTH)

    model_name = settings.DOCUMENT_QA_MODEL_NAME
    prompt = PROMPT.format(question=question, document=document)
    content = await llm_acall(
        model_name=model_name, messages=[ChatMessage(role="user", content=prompt)]
    )
    return content.strip()
