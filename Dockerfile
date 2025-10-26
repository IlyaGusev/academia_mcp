FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN apt-get update
RUN apt-get install -y \
    curl \
    build-essential \
    gcc \
    make \
    g++ \
    git \
    python3-dev \
    libffi-dev \
    openssl \
    perl \
    texlive \
    texlive-xetex \
    texlive-luatex \
    ghostscript \
    fontconfig

COPY . /app
RUN uv sync --no-dev && rm -rf /root/.cache/uv

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []
CMD ["python", "-m", "academia_mcp"]
