FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /dbt

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

COPY dbt_project.yml profiles.yml ./
COPY models/ ./models/
COPY macros/ ./macros/
COPY seeds/ ./seeds/
COPY snapshots/ ./snapshots/
COPY tests/ ./tests/
COPY dagster_defs/ ./dagster_defs/

RUN uv run dbt parse

ENV PATH="/dbt/.venv/bin:$PATH"

CMD ["dagster", "code-server", "start", "--host", "0.0.0.0", "--port", "3031", "--module-name", "dagster_defs.definitions"]
