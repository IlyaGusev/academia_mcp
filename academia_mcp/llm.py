import os
from typing import List, Dict, Any

from pydantic import BaseModel
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage


class ChatMessage(BaseModel):  # type: ignore
    role: str
    content: str | List[Dict[str, Any]]


ChatMessages = List[ChatMessage]


async def llm_acall(model_name: str, messages: ChatMessages, **kwargs: Any) -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    assert key, "Please set OPENROUTER_API_KEY in the environment variables"
    base_url = os.getenv("BASE_URL", "https://openrouter.ai/api/v1")

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
