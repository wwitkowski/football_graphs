FROM python:3.12-slim-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/0.6.6/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && \
    cp /root/.local/bin/uv /usr/local/bin/uv && \
    if [ -f /root/.local/bin/uvx ]; then cp /root/.local/bin/uvx /usr/local/bin/uvx; fi && \
    rm /uv-installer.sh

COPY ./scripts /app/scripts
COPY ./data_backend /app/data_backend
COPY pyproject.toml /app
COPY uv.lock /app

WORKDIR /app

RUN uv sync --frozen

RUN useradd --create-home --shell /bin/bash app && \
    mkdir -p /home/app/.aws && \
    chown -R app:app /app /home/app

USER app
