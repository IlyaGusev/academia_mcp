import pytest
import asyncio
import threading
import time
from pathlib import Path
from contextlib import suppress
from typing import Generator

import uvicorn
from sse_starlette.sse import AppStatus

from academia_mcp.server import create_server
from academia_mcp.settings import settings

settings.WORKSPACE_DIR = Path(__file__).parent / "workdir"


@pytest.fixture
def test_image_url() -> str:
    return "https://arxiv.org/html/2409.06820v4/extracted/6347978/pingpong_v3.drawio.png"


@pytest.fixture
def test_audio_url() -> str:
    return "https://raw.githubusercontent.com/voxserv/audio_quality_testing_samples/refs/heads/master/testaudio/16000/test01_20s.wav"


def reset_app_status() -> None:
    AppStatus.should_exit = False
    if hasattr(AppStatus, "should_exit_event"):
        AppStatus.should_exit_event = None


class MCPServerTest:
    def __init__(self, port: int, host: str = "0.0.0.0") -> None:
        self.port = port
        self.host = host
        server = create_server(port=port, host=host)
        app = server.streamable_http_app()
        config = uvicorn.Config(
            app,
            host=host,
            port=self.port,
            log_level="error",
            access_log=False,
            lifespan="on",
            ws="none",
        )
        self.server: uvicorn.Server = uvicorn.Server(config)
        self._thread: threading.Thread | None = None
        self._started = threading.Event()

    def start(self) -> None:
        def _run() -> None:
            async def _serve() -> None:
                assert self.server is not None
                await self.server.serve()

            with suppress(asyncio.CancelledError):
                asyncio.run(_serve())

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

        deadline = time.time() + 30
        while time.time() < deadline:
            if self.server.started:
                self._started.set()
                break
            time.sleep(0.05)
        if not self._started.is_set():
            raise RuntimeError("Mock MCP server failed to start within 30 s")

    def stop(self) -> None:
        if self.server:
            self.server.should_exit = True
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        reset_app_status()
        self.app = None

    def is_running(self) -> bool:
        return self._started.is_set() and self._thread is not None and self._thread.is_alive()


@pytest.fixture(scope="function")
def mcp_server_test() -> Generator[MCPServerTest, None, None]:
    server = MCPServerTest(port=6000)
    server.start()
    yield server
    server.stop()
