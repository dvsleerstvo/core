FROM python:3.13-slim

env PYTHONUNBUFFERED 1
WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-dev \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml /app
COPY uv.lock /app

RUN uv sync --frozen --no-cache

COPY . /app

CMD ["uv", "run", "main.py"]