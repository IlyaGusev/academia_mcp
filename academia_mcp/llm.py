from typing import Any, Dict, List, TypeVar

from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from pydantic import BaseModel

from academia_mcp.settings import settings

T = TypeVar("T", bound=BaseModel)


class ChatMessage(BaseModel):  # type: ignore
    role: str
    content: str | List[Dict[str, Any]]


ChatMessages = List[ChatMessage]


async def llm_acall(model_name: str, messages: ChatMessages, **kwargs: Any) -> str:
    key = settings.OPENROUTER_API_KEY
    assert key, "Please set OPENROUTER_API_KEY in the environment variables"
    base_url = settings.BASE_URL

    client = AsyncOpenAI(base_url=base_url, api_key=key)
    response: ChatCompletionMessage = (
        (
            await client.chat.completions.create(
                model=model_name,
                messages=messages,
                **kwargs,
            )
        )
        .choices[0]
        .message
    )
    assert response.content, "Response content is None"
    return response.content


async def llm_acall_structured(
    model_name: str,
    messages: ChatMessages,
    response_format: type[T],
    num_parsing_retries: int = 3,
    **kwargs: Any,
) -> T:
    key = settings.OPENROUTER_API_KEY
    assert key, "Please set OPENROUTER_API_KEY in the environment variables"
    base_url = settings.BASE_URL

    client = AsyncOpenAI(base_url=base_url, api_key=key)
    converted_messages = [message.model_dump() for message in messages]
    for retry_index in range(num_parsing_retries):
        try:
            structured_response: T | None = (
                (
                    await client.chat.completions.parse(
                        model=model_name,
                        messages=converted_messages,
                        response_format=response_format,
                        **kwargs,
                    )
                )
                .choices[0]
                .message.parsed
            )
            assert structured_response
            break
        except Exception:
            if retry_index == num_parsing_retries - 1:
                raise
            continue
    assert structured_response
    return structured_response
