FROM python:3.11-slim

# Install dbt-athena
RUN pip install --no-cache-dir \
    dbt-athena-community==1.7.2 \
    boto3==1.34.51

# Set working directory
WORKDIR /dbt

# Copy dbt project
COPY . /dbt/

# Default command
CMD ["dbt", "run"]
