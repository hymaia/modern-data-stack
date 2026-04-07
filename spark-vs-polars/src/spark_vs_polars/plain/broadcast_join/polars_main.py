import polars as pl

from spark_vs_polars.config import Config


def main():
    config = Config()
    storage_options = {"aws_region": "eu-west-1"}

    schema = pl.Schema(
        {
            "uid": pl.String(),
            "dt": pl.String(),
            "entity_type": pl.String(),
            "order_id": pl.String(),
            "user_id": pl.String(),
            "placed_at": pl.String(),
            "updated_at": pl.String(),
            "delivered_at": pl.String(),
            "item_count": pl.Int32(),
            "cancellation_reason": pl.String(),
        }
    )

    small_df = pl.read_ndjson(
        config.INPUT_BROADCAST_JOIN_FILE, storage_options=storage_options
    )

    df = pl.scan_ndjson(
        f"{config.INPUT_FILE}/**/*.json", schema=schema, storage_options=storage_options
    )

    res = (
        df.with_columns(
            [
                pl.col("delivered_at").str.to_date(format="%Y-%m-%d").cast(pl.Datetime),
                pl.col("placed_at").str.to_datetime(format="%Y-%m-%dT%H:%M:%SZ"),
            ]
        )
        .with_columns(
            [
                (
                    (pl.col("delivered_at") - pl.col("placed_at")).dt.total_seconds()
                ).alias("delivery_delay_sec"),
                pl.col("delivered_at").dt.year().alias("year"),
                pl.col("delivered_at").dt.month().alias("month"),
                pl.col("delivered_at").dt.day().alias("day"),
            ]
        )
        .with_columns(
            [
                (pl.col("delivery_delay_sec") / 3600)
                .round(0)
                .cast(pl.Int32)
                .alias("delivery_delay_hour"),
            ]
        )
        .join(pl.LazyFrame(small_df), on="cancellation_reason", how="inner")
        .filter(pl.col("delivered_at").dt.year() == 2025)
    )
    res.sink_parquet(
        pl.PartitionBy(config.OUTPUT_FILE, key=["year", "month", "day"]),
        storage_options=storage_options,
    )


if __name__ == "__main__":
    main()
