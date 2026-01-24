import json
import logging
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from academia_mcp.auth.models import TokenMetadata, TokenStore
from academia_mcp.settings import settings

logger = logging.getLogger(__name__)


def generate_token() -> str:
    return f"mcp_{secrets.token_hex(16)}"


def load_tokens(path: Optional[Path] = None) -> TokenStore:
    if path is None:
        path = settings.TOKENS_FILE

    if not path.exists():
        logger.info(f"Token file {path} does not exist, creating empty store")
        return TokenStore()

    try:
        with open(path, "r") as f:
            data = json.load(f)
            return TokenStore(**data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse token file {path}: {e}")
        backup_path = path.with_suffix(".bak")
        if path.exists():
            path.rename(backup_path)
            logger.info(f"Corrupted token file backed up to {backup_path}")
        return TokenStore()
    except Exception as e:
        logger.error(f"Failed to load tokens from {path}: {e}")
        raise


def save_tokens(store: TokenStore, path: Optional[Path] = None) -> None:
    if path is None:
        path = settings.TOKENS_FILE

    path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = path.with_suffix(".tmp")
    try:
        with open(temp_path, "w") as f:
            json.dump(store.model_dump(mode="json"), f, indent=2, default=str)
        temp_path.replace(path)

        try:
            import os

            os.chmod(path, 0o600)
        except Exception as e:
            logger.warning(f"Failed to set file permissions on {path}: {e}")

    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        logger.error(f"Failed to save tokens to {path}: {e}")
        raise


def issue_token(
    client_id: str,
    scopes: Optional[List[str]] = None,
    expires_days: Optional[int] = None,
    description: str = "",
    path: Optional[Path] = None,
) -> TokenMetadata:
    if scopes is None:
        scopes = ["*"]

    token_id = generate_token()

    while True:
        store = load_tokens(path)
        if token_id not in store.tokens:
            break
        logger.warning(f"Token collision detected for {token_id}, regenerating")
        token_id = generate_token()

    expires_at = None
    if expires_days is not None:
        expires_at = datetime.utcnow() + timedelta(days=expires_days)

    metadata = TokenMetadata(
        token_id=token_id,
        client_id=client_id,
        scopes=scopes,
        issued_at=datetime.utcnow(),
        expires_at=expires_at,
        description=description,
        revoked=False,
        last_used=None,
    )

    store.tokens[token_id] = metadata
    save_tokens(store, path)

    logger.info(f"Issued token for client_id={client_id}, expires={expires_at}")
    return metadata


def validate_token(token: str, path: Optional[Path] = None) -> Optional[TokenMetadata]:
    if not token.startswith("mcp_"):
        return None

    store = load_tokens(path)

    if token not in store.tokens:
        return None

    metadata = store.tokens[token]

    if metadata.revoked:
        logger.debug(f"Token {token[:16]}... is revoked")
        return None

    if metadata.expires_at is not None and datetime.utcnow() > metadata.expires_at:
        logger.debug(f"Token {token[:16]}... has expired")
        return None

    return metadata


def list_tokens(path: Optional[Path] = None) -> List[TokenMetadata]:
    store = load_tokens(path)
    return [metadata for metadata in store.tokens.values() if not metadata.revoked]


def revoke_token(token_id: str, path: Optional[Path] = None) -> bool:
    store = load_tokens(path)

    if token_id not in store.tokens:
        logger.warning(f"Token {token_id} not found")
        return False

    store.tokens[token_id].revoked = True
    save_tokens(store, path)

    logger.info(f"Revoked token {token_id[:16]}...")
    return True


def update_last_used(token_id: str, path: Optional[Path] = None) -> None:
    try:
        store = load_tokens(path)
        if token_id in store.tokens:
            store.tokens[token_id].last_used = datetime.utcnow()
            save_tokens(store, path)
    except Exception as e:
        logger.warning(f"Failed to update last_used for {token_id[:16]}...: {e}")
