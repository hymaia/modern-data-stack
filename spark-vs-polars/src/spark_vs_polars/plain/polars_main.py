import polars as pl

from spark_vs_polars.config import Config


def main():
    config = Config()
    storage_options = {
        "aws_region": "eu-west-1",
    }

    schema = pl.Schema({
        "uid":                 pl.String(),
        "dt":                  pl.String(),
        "entity_type":         pl.String(),
        "order_id":            pl.String(),
        "user_id":             pl.String(),
        "placed_at":           pl.String(),
        "updated_at":          pl.String(),
        "delivered_at":        pl.String(),
        "item_count":          pl.Int32(),
        "cancellation_reason": pl.String(),
    })

    df = pl.scan_ndjson(f"{config.INPUT_FILE}/**/*.json", schema=schema, storage_options=storage_options)
    res = (
        df.with_columns([
            pl.col("delivered_at").str.to_date(format="%Y-%m-%d").cast(pl.Datetime),
            pl.col("placed_at").str.to_datetime(format="%Y-%m-%dT%H:%M:%SZ"),
        ])
        .with_columns([
            ((pl.col("delivered_at") - pl.col("placed_at")).dt.total_seconds()).alias("delivery_delay_sec"),
        ])
        .with_columns([
            (pl.col("delivery_delay_sec") / 3600).round(0).cast(pl.Int32).alias("delivery_delay_hour"),
        ])
        .group_by("cancellation_reason", "delivery_delay_hour")
        .agg([
            pl.len().alias("count"),
            pl.col("delivery_delay_sec").mean().alias("average_delivered_delay"),
        ])
    )
    res.sink_parquet(config.OUTPUT_FILE, storage_options=storage_options)


if __name__ == "__main__":
    main()
