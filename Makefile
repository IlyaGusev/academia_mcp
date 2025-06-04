.PHONY: black style validate test install serve

install:
	uv pip install -e .

black:
	uv run black academia_mcp --line-length 100

validate:
	uv run black academia_mcp --line-length 100
	uv run flake8 academia_mcp
	uv run mypy academia_mcp --strict --explicit-package-bases

test:
	uv run pytest -s
