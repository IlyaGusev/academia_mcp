from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TokenMetadata(BaseModel):  # type: ignore
    token_id: str = Field(description="Unique token identifier (mcp_[hex])")
    client_id: str = Field(description="Human-readable client identifier")
    scopes: List[str] = Field(default_factory=lambda: ["*"], description="Access scopes")
    issued_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(), description="Token issuance timestamp"
    )
    expires_at: Optional[datetime] = Field(
        default=None, description="Expiration time (None = never)"
    )
    description: str = Field(default="", description="Optional description")
    revoked: bool = Field(default=False, description="Whether token is revoked")
    last_used: Optional[datetime] = Field(default=None, description="Last time token was used")


class TokenStore(BaseModel):  # type: ignore
    tokens: Dict[str, TokenMetadata] = Field(
        default_factory=dict, description="Map of token_id to metadata"
    )
    version: str = Field(default="1.0", description="Storage format version")
