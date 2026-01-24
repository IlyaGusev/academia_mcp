from typing import Any

import fire  # type: ignore

from .auth import cli as auth_cli
from .server import run


class CLI:
    def __init__(self) -> None:
        self.auth = auth_cli.AuthCLI()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return run(*args, **kwargs)

    def run(self, *args: Any, **kwargs: Any) -> Any:
        return run(*args, **kwargs)


def main() -> None:
    fire.Fire(CLI)
