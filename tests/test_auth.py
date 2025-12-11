from datetime import datetime, timedelta

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from academia_mcp.auth.middleware import BearerTokenAuthMiddleware
from academia_mcp.auth.models import TokenMetadata, TokenStore
from academia_mcp.auth.token_manager import (
    generate_token,
    issue_token,
    list_tokens,
    load_tokens,
    revoke_token,
    save_tokens,
    validate_token,
)
from academia_mcp.settings import settings


def test_auth_generate_token_format() -> None:
    token = generate_token()
    assert token.startswith("mcp_")
    assert len(token) == 36


def test_auth_issue_token(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    metadata = issue_token(
        client_id="test-client",
        scopes=["read", "write"],
        expires_days=None,
        description="Test token",
        path=tokens_file,
    )

    assert metadata.token_id.startswith("mcp_")
    assert metadata.client_id == "test-client"
    assert metadata.scopes == ["read", "write"]
    assert metadata.description == "Test token"
    assert metadata.expires_at is None
    assert metadata.revoked is False
    assert metadata.last_used is None

    assert tokens_file.exists()


def test_auth_issue_token_with_expiration(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    metadata = issue_token(
        client_id="test-client",
        expires_days=30,
        path=tokens_file,
    )

    assert metadata.expires_at is not None
    expected_expiry = datetime.utcnow() + timedelta(days=30)
    assert abs((metadata.expires_at - expected_expiry).total_seconds()) < 5


def test_auth_load_save_tokens(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    store = TokenStore()
    metadata = TokenMetadata(
        token_id="mcp_test123",
        client_id="test-client",
        scopes=["*"],
        issued_at=datetime.utcnow(),
    )
    store.tokens["mcp_test123"] = metadata

    save_tokens(store, tokens_file)
    assert tokens_file.exists()

    loaded_store = load_tokens(tokens_file)
    assert "mcp_test123" in loaded_store.tokens
    assert loaded_store.tokens["mcp_test123"].client_id == "test-client"


def test_auth_load_tokens_missing_file(tmp_path: object) -> None:
    tokens_file = tmp_path / "nonexistent.json"  # type: ignore

    store = load_tokens(tokens_file)
    assert len(store.tokens) == 0


def test_auth_load_tokens_corrupted_file(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore
    tokens_file.write_text("{invalid json")

    store = load_tokens(tokens_file)
    assert len(store.tokens) == 0

    backup_file = tmp_path / "tokens.bak"  # type: ignore
    assert backup_file.exists()


def test_auth_validate_token_success(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    metadata = issue_token(
        client_id="test-client",
        path=tokens_file,
    )

    validated = validate_token(metadata.token_id, tokens_file)
    assert validated is not None
    assert validated.client_id == "test-client"


def test_auth_validate_token_invalid_format(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    validated = validate_token("invalid_token", tokens_file)
    assert validated is None


def test_auth_validate_token_not_found(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    validated = validate_token("mcp_nonexistent", tokens_file)
    assert validated is None


def test_auth_validate_token_expired(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    store = TokenStore()
    expired_time = datetime.utcnow() - timedelta(days=1)
    metadata = TokenMetadata(
        token_id="mcp_expired",
        client_id="test-client",
        scopes=["*"],
        issued_at=datetime.utcnow() - timedelta(days=2),
        expires_at=expired_time,
    )
    store.tokens["mcp_expired"] = metadata
    save_tokens(store, tokens_file)

    validated = validate_token("mcp_expired", tokens_file)
    assert validated is None


def test_auth_validate_token_revoked(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    metadata = issue_token(client_id="test-client", path=tokens_file)
    revoke_token(metadata.token_id, tokens_file)

    validated = validate_token(metadata.token_id, tokens_file)
    assert validated is None


def test_auth_list_tokens(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    issue_token(client_id="client1", path=tokens_file)
    issue_token(client_id="client2", path=tokens_file)
    metadata3 = issue_token(client_id="client3", path=tokens_file)

    revoke_token(metadata3.token_id, tokens_file)

    tokens = list_tokens(tokens_file)
    assert len(tokens) == 2
    client_ids = [t.client_id for t in tokens]
    assert "client1" in client_ids
    assert "client2" in client_ids
    assert "client3" not in client_ids


def test_auth_revoke_token(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    metadata = issue_token(client_id="test-client", path=tokens_file)

    success = revoke_token(metadata.token_id, tokens_file)
    assert success is True

    store = load_tokens(tokens_file)
    assert store.tokens[metadata.token_id].revoked is True


def test_auth_revoke_token_not_found(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore

    success = revoke_token("mcp_nonexistent", tokens_file)
    assert success is False


@pytest.mark.asyncio
async def test_auth_middleware_valid_token(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore
    settings.TOKENS_FILE = tokens_file

    metadata = issue_token(client_id="test-client", path=tokens_file)

    app = Starlette()
    app.add_middleware(BearerTokenAuthMiddleware)

    @app.route("/test")
    async def test_endpoint(request: object) -> JSONResponse:
        return JSONResponse({"message": "success"})

    client = TestClient(app)
    response = client.get("/test", headers={"Authorization": f"Bearer {metadata.token_id}"})

    assert response.status_code == 200
    assert response.json() == {"message": "success"}


@pytest.mark.asyncio
async def test_auth_middleware_missing_header(tmp_path: object) -> None:
    app = Starlette()
    app.add_middleware(BearerTokenAuthMiddleware)

    @app.route("/test")
    async def test_endpoint(request: object) -> JSONResponse:
        return JSONResponse({"message": "success"})

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_middleware_invalid_format(tmp_path: object) -> None:
    app = Starlette()
    app.add_middleware(BearerTokenAuthMiddleware)

    @app.route("/test")
    async def test_endpoint(request: object) -> JSONResponse:
        return JSONResponse({"message": "success"})

    client = TestClient(app)
    response = client.get("/test", headers={"Authorization": "InvalidFormat"})

    assert response.status_code == 401
    assert "Invalid Authorization header format" in response.json()["error"]


@pytest.mark.asyncio
async def test_auth_middleware_expired_token(tmp_path: object) -> None:
    tokens_file = tmp_path / "tokens.json"  # type: ignore
    settings.TOKENS_FILE = tokens_file

    store = TokenStore()
    expired_time = datetime.utcnow() - timedelta(days=1)
    metadata = TokenMetadata(
        token_id="mcp_expired_token",
        client_id="test-client",
        scopes=["*"],
        issued_at=datetime.utcnow() - timedelta(days=2),
        expires_at=expired_time,
    )
    store.tokens["mcp_expired_token"] = metadata
    save_tokens(store, tokens_file)

    app = Starlette()
    app.add_middleware(BearerTokenAuthMiddleware)

    @app.route("/test")
    async def test_endpoint(request: object) -> JSONResponse:
        return JSONResponse({"message": "success"})

    client = TestClient(app)
    response = client.get("/test", headers={"Authorization": "Bearer mcp_expired_token"})

    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["error"]


@pytest.mark.asyncio
async def test_auth_middleware_options_bypass(tmp_path: object) -> None:
    app = Starlette()
    app.add_middleware(BearerTokenAuthMiddleware)

    @app.route("/test", methods=["OPTIONS"])
    async def test_endpoint(request: object) -> JSONResponse:
        return JSONResponse({"message": "success"})

    client = TestClient(app)
    response = client.options("/test")

    assert response.status_code == 200
