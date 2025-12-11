import fire  # type: ignore

from .auth import cli as auth_cli
from .server import run


class CLI:
    def __init__(self) -> None:
        self.run = run
        self.auth = auth_cli.AuthCLI()


def main() -> None:
    fire.Fire(CLI)
