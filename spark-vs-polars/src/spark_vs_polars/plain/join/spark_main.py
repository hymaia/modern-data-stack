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
    spark = SparkSession.builder.appName("plain_spark").getOrCreate()
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

    join_df = spark.read.json(config.INPUT_JOIN_FILE) \
        .withColumn("placed_at", f.to_timestamp(f.col("placed_at"), "yyyy-MM-dd'T'HH:mm:ss'Z'"))
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
        .join(join_df, "placed_at")
        .filter(f.year(f.col("delivered_at")) == 2025)
        .withColumn("year", f.year(f.col("delivered_at")))
        .withColumn("month", f.month(f.col("delivered_at")))
        .withColumn("day", f.dayofmonth(f.col("delivered_at")))
    )

    res.write.mode("overwrite").partitionBy("year", "month", "day").parquet(
        config.OUTPUT_FILE
    )


if __name__ == "__main__":
    main()
