from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BASE_URL: str = "https://openrouter.ai/api/v1"

    OPENROUTER_API_KEY: str = ""
    TAVILY_API_KEY: Optional[str] = None
    EXA_API_KEY: Optional[str] = None
    BRAVE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    REVIEW_MODEL_NAME: str = "gpt-5"
    BITFLIP_MODEL_NAME: str = "deepseek/deepseek-chat-v3-0324"
    BITFLIP_MAX_COMPLETION_TOKENS: int = 16384
    DOCUMENT_QA_MODEL_NAME: str = "deepseek/deepseek-chat-v3-0324"
    DOCUMENT_QA_QUESTION_MAX_LENGTH: int = 10000
    DOCUMENT_QA_DOCUMENT_MAX_LENGTH: int = 200000
    DESCRIBE_IMAGE_MODEL_NAME: str = "gpt-4.1"

    PORT: int = 5056
    WORKSPACE_DIR: Optional[Path] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        extra="ignore",
    )


settings = Settings()
