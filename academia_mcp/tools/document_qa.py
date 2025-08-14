import os
from typing import List, Any, Dict, cast
from dotenv import load_dotenv

from pydantic import BaseModel
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionMessage


load_dotenv()

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions about documents accurately and concisely."
)
PROMPT = """Please answer the following questions based solely on the provided document.
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


def document_qa(
    document: str,
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
    assert document and document.strip(), "Please provide non-empty 'document'"

    base_url = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")
    key = os.getenv("OPENROUTER_API_KEY", "")
    assert key, "Please set OPENROUTER_API_KEY in the environment variables"
    model_name = os.getenv("DOCUMENT_QA_MODEL_NAME", "deepseek/deepseek-chat-v3-0324")

    messages: ChatMessages = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(
            role="user",
            content=PROMPT.format(question=question, document=document),
        ),
    ]

    sdk_messages = [
        cast(ChatCompletionMessageParam, m.model_dump(exclude_none=True)) for m in messages
    ]
    client = OpenAI(base_url=base_url, api_key=key)
    response: ChatCompletionMessage = (
        client.chat.completions.create(
            model=model_name,
            messages=sdk_messages,
            temperature=0.0,
        )
        .choices[0]
        .message
    )

    if response.content is None:
        raise Exception("Response content is None")
    return response.content.strip()
