FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv export --no-dev --no-emit-project -o requirements.txt


FROM apache/spark:4.1.1-python3

USER root

WORKDIR /app

COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ADD https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.4.2/hadoop-aws-3.4.2.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/software/amazon/awssdk/bundle/2.40.17/bundle-2.40.17.jar /opt/spark/jars/
ADD https://repo1.maven.org/maven2/org/apache/spark/spark-hadoop-cloud_2.13/4.1.1/spark-hadoop-cloud_2.13-4.1.1.jar /opt/spark/jars/

RUN chown spark:spark /opt/spark/jars/hadoop-aws-3.4.2.jar /opt/spark/jars/bundle-2.40.17.jar /opt/spark/jars/spark-hadoop-cloud_2.13-4.1.1.jar
RUN chmod 644 /opt/spark/jars/hadoop-aws-3.4.2.jar /opt/spark/jars/bundle-2.40.17.jar /opt/spark/jars/spark-hadoop-cloud_2.13-4.1.1.jar

COPY src/ ./src/

USER 185

ENV PYTHONPATH="/app/src"
