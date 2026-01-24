import asyncio
import logging
from collections.abc import Awaitable
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from academia_mcp.auth.token_manager import update_last_used, validate_token

logger = logging.getLogger(__name__)


class BearerTokenAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        token = None

        api_key = request.query_params.get("apiKey")
        if api_key:
            token = api_key
            logger.debug("Using token from apiKey query parameter")
        else:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                logger.debug("Missing Authorization header and apiKey query parameter")
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Missing authentication. Provide either Authorization header or apiKey query parameter"
                    },
                    headers={"WWW-Authenticate": 'Bearer realm="MCP API"'},
                )

            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                logger.debug(f"Invalid Authorization header format: {auth_header}")
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Invalid Authorization header format. Expected: Bearer <token>"
                    },
                    headers={"WWW-Authenticate": 'Bearer realm="MCP API"'},
                )

            token = parts[1]
            logger.debug("Using token from Authorization header")

        metadata = validate_token(token)
        if metadata is None:
            logger.debug(f"Invalid or expired token: {token[:16]}...")
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or expired token"},
                headers={"WWW-Authenticate": 'Bearer realm="MCP API"'},
            )

        request.state.token_metadata = metadata

        asyncio.create_task(self._update_last_used_async(token))

        logger.debug(f"Authenticated request for client_id={metadata.client_id}")
        return await call_next(request)

    async def _update_last_used_async(self, token: str) -> None:
        try:
            update_last_used(token)
        except Exception as e:
            logger.warning(f"Failed to update last_used for token: {e}")
