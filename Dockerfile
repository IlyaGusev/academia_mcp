FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN echo "net.ipv6.conf.all.disable_ipv6 = 1" >> /etc/sysctl.conf && \
    echo "net.ipv6.conf.default.disable_ipv6 = 1" >> /etc/sysctl.conf && \
    echo "net.ipv6.conf.lo.disable_ipv6 = 1" >> /etc/sysctl.conf && \
    echo "net.ipv6.conf.eth0.disable_ipv6 = 1" >> /etc/sysctl.conf

RUN echo "options single-request-reopen" >> /etc/resolv.conf && \
    mkdir -p /etc/gai.conf.d && \
    echo "precedence ::ffff:0:0/96  100" > /etc/gai.conf

RUN apk add --no-cache libstdc++ libffi openssl git
RUN apk add --no-cache --virtual .build-deps \
    build-base python3-dev libffi-dev openssl-dev linux-headers rust cargo
RUN apk add --no-cache \
    perl \
    texlive \
    texlive-xetex \
    texlive-luatex \
    ghostscript \
    fontconfig \
    ttf-dejavu

COPY . /app
RUN  uv sync --no-dev
RUN apk del .build-deps && rm -rf /root/.cache/uv

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []
CMD ["python", "-m", "academia_mcp"]
