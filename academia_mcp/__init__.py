import fire  # type: ignore

from .server import run


def main() -> None:
    fire.Fire(run)
