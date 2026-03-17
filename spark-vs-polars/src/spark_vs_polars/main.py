from pyspark.sql import SparkSession, DataFrame

from src.spark_vs_polars.config import Config
from pyspark.sql import functions as f

def main():
    spark: SparkSession = SparkSession.builder.appName("spark on dagster").getOrCreate()
    config = Config()

    df: DataFrame = spark.read.parquet(config.INPUT_FILE)
    renamed: DataFrame = rename_df(df)

    renamed.write.parquet(config.OUTPUT_FILE)


def rename_df(df: DataFrame) -> DataFrame:
    return df.select(
        f.col("sha").alias("commit_sha"),
        f.get_json_object("commit", "$.author.name").alias("author_name"),
        f.get_json_object("commit", "$.author.email").alias("author_email"),
        f.to_timestamp(
            f.get_json_object("commit", "$.author.date"),
            "yyyy-MM-dd'T'HH:mm:ss'Z'"
        ).alias("committed_at"),
        f.get_json_object("commit", "$.message").alias("message"),
        f.get_json_object("author", "$.login").alias("author_login"),
        f.col("repository").alias("repository_name"),
        f.col("html_url").alias("commit_url"),
        f.col("branch"),
    )


if __name__ == "__main__":
    main()
