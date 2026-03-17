FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv export --no-dev --no-emit-project -o requirements.txt


FROM apache/spark:4.1.1-python3

USER root

WORKDIR /app

COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ADD https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.2/hadoop-aws-3.4.2.jar /app/jars/
ADD https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.40.17/bundle-2.40.17.jar /app/jars/
RUN chown -R 185:185 /app

USER 185

ENV PYTHONPATH="/app"
