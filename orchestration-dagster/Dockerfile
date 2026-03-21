FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen
COPY src/ ./src/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
EXPOSE 3030

CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "3030", "-m", "orchestration_dagster.definitions"]
