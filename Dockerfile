FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
ADD https://astral.sh/uv/0.6.6/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

ADD ./scripts /app/scripts
ADD ./data_backend /app/data_backend
ADD pyproject.toml /app
ADD uv.lock /app

WORKDIR /app

RUN uv sync --frozen
