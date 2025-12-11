.PHONY: black style validate test install serve

install:
	uv pip install -e .

black:
	uv run isort academia_mcp tests
	uv run black academia_mcp tests --line-length 100

validate:
	uv run isort academia_mcp tests
	uv run black academia_mcp tests --line-length 100
	uv run flake8 academia_mcp tests
	uv run mypy academia_mcp tests --strict --explicit-package-bases

test:
	uv run pytest -s ./tests

publish:
	uv build && uv publish
