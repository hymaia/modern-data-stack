import polars as pl
from src.spark_vs_polars.config import Config


def main():
    config = Config()
    storage_options = {
        "aws_region": "eu-west-1",
    }

    df = pl.scan_parquet(
        config.INPUT_FILE,
        storage_options=storage_options,
        missing_columns="insert",
        extra_columns="ignore",
    )
    renamed = rename_df(df)
    renamed.sink_parquet(config.OUTPUT_FILE)


def rename_df(df: pl.LazyFrame) -> pl.LazyFrame:
    return df.select(
        pl.col("sha").alias("commit_sha"),
        pl.col("commit").str.json_path_match("$.author.name").alias("author_name"),
        pl.col("commit").str.json_path_match("$.author.email").alias("author_email"),
        pl.col("commit").str.json_path_match("$.author.date").str.to_datetime("%Y-%m-%dT%H:%M:%SZ").alias("committed_at"),
        pl.col("commit").str.json_path_match("$.message").alias("message"),
        pl.col("author").str.json_path_match("$.login").alias("author_login"),
        pl.col("repository").alias("repository_name"),
        pl.col("html_url").alias("commit_url"),
        pl.col("branch"),
    )


if __name__ == "__main__":
    main()
