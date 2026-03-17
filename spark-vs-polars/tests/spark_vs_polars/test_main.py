from pyspark.testing import assertDataFrameEqual
from pyspark.sql import Row
from datetime import datetime
from src.spark_vs_polars.main import rename_df


def test_rename_df(spark):
    input_df = spark.createDataFrame([
        Row(
            sha="abc123",
            commit='{"author": {"name": "John Doe", "email": "john@example.com", "date": "2024-01-15T10:30:00Z"}, "message": "fix: bug fix"}',
            author='{"login": "johndoe"}',
            repository="my-repo",
            html_url="https://github.com/my-repo/commit/abc123",
            branch="main",
        )
    ])

    expected_df = spark.createDataFrame([
        Row(
            commit_sha="abc123",
            author_name="John Doe",
            author_email="john@example.com",
            committed_at=datetime(2024, 1, 15, 10, 30, 0),
            message="fix: bug fix",
            author_login="johndoe",
            repository_name="my-repo",
            commit_url="https://github.com/my-repo/commit/abc123",
            branch="main",
        )
    ])

    assertDataFrameEqual(rename_df(input_df), expected_df)
