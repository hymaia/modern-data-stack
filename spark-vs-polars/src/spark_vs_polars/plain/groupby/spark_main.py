from pyspark.sql import SparkSession
from pyspark.sql import functions as f
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    TimestampType,
    IntegerType,
)

from spark_vs_polars.config import Config


def main():
    spark = (
        SparkSession.builder
        .appName("plain_spark")
        .config("spark.sql.parquet.compression.codec", "zstd")
        .config("spark.io.compression.zstd.level", "3")
        .config("spark.sql.adaptive.enabled", "true")
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
        .getOrCreate()
    )
    config = Config()

    schema = StructType(
        [
            StructField("uid", StringType(), nullable=False),
            StructField("entity_type", StringType(), nullable=False),
            StructField("order_id", StringType(), nullable=False),
            StructField("user_id", StringType(), nullable=False),
            StructField("placed_at", TimestampType(), nullable=False),
            StructField("updated_at", TimestampType(), nullable=False),
            StructField("delivered_at", TimestampType(), nullable=False),
            StructField("item_count", IntegerType(), nullable=False),
            StructField("cancellation_reason", StringType(), nullable=False),
        ]
    )

    df = spark.read.schema(schema).json(config.INPUT_FILE)
    res = (
        df.withColumn("delivered_at", f.to_timestamp(f.col("delivered_at")))
        .withColumn("placed_at", f.to_timestamp(f.col("placed_at")))
        .withColumn(
            "delivery_duration_seconds",
            f.unix_timestamp("delivered_at") - f.unix_timestamp("placed_at"),
        )
        .withColumn(
            "delivery_delay_hour",
            f.round(
                (f.unix_timestamp("delivered_at") - f.unix_timestamp("placed_at"))
                / 3600,
                0,
            ).cast("int"),
        )
        .withColumn(
            "delivery_delay_sec",
            f.unix_timestamp("delivered_at") - f.unix_timestamp("placed_at"),
        )
        .groupBy("cancellation_reason", "delivery_delay_hour")
        .agg(
            f.count("*").alias("count"),
            f.avg("delivery_delay_sec").alias("average_delivered_delay"),
        )
    )
    res.write.mode("overwrite").parquet(config.OUTPUT_FILE)


if __name__ == "__main__":
    main()
