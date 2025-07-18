FROM python:3.12-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/0.6.6/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

COPY ./scripts /app/scripts
COPY ./data_backend /app/data_backend
COPY pyproject.toml /app
COPY uv.lock /app

WORKDIR /app

RUN uv sync --frozen
