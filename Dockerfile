# Dockerfile
# Use a Python image with uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-alpine

# Install the project into `/app`
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Runtime libs
RUN apk add --no-cache libstdc++ libffi openssl git
RUN apk add --no-cache --virtual .build-deps \
    build-base python3-dev libffi-dev openssl-dev linux-headers rust cargo

COPY . /app
RUN  uv sync --no-dev
RUN apk del .build-deps && rm -rf /root/.cache/uv

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []

# Run the application directly using the venv Python
CMD ["python", "-m", "academia_mcp"]
