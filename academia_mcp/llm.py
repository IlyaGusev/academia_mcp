from typing import List, Dict, Any

from pydantic import BaseModel
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from academia_mcp.settings import settings


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
