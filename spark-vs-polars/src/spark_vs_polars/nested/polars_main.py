"""
transform_dynamo.py
===================
Lit les fichiers NDJSON partitionnés (output/dt=YYYY-MM-DD/data.ndjson),
applique des transformations Polars full-lazy et écrit en Parquet partitionné.

Usage:
    pip install polars
    python transform_dynamo.py --input output --output parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def scan_all(source: Path) -> pl.LazyFrame:
    """
    Scan lazy de tous les fichiers NDJSON.
    On injecte la colonne 'dt' depuis le nom du dossier parent
    en passant par scan_ndjson sur chaque partition et en concaténant.
    Polars ne supportant pas encore le hive_partitioning sur scan_ndjson,
    on reconstruit la colonne dt manuellement.
    """
    partitions = sorted(source.glob("dt=*/data.ndjson"))
    if not partitions:
        raise FileNotFoundError(f"Aucun fichier data.ndjson dans {source}")

    frames = []
    for p in partitions:
        day = p.parent.name.replace("dt=", "")
        lf = (
            pl.scan_ndjson(p, infer_schema_length=10_000)
            .with_columns(pl.lit(day).alias("dt"))
        )
        frames.append(lf)

    return pl.concat(frames, how="diagonal_relaxed")


# ---------------------------------------------------------------------------
# Split par entity_type
# ---------------------------------------------------------------------------

def split(lf: pl.LazyFrame, entity_type: str) -> pl.LazyFrame:
    return lf.filter(pl.col("entity_type") == entity_type)


# ---------------------------------------------------------------------------
# Enrichissements
# ---------------------------------------------------------------------------

def enrich_orders(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.with_columns([
        pl.when(pl.col("total_amount") < 50).then(pl.lit("low"))
        .when(pl.col("total_amount") < 200).then(pl.lit("mid"))
        .when(pl.col("total_amount") < 500).then(pl.lit("high"))
        .otherwise(pl.lit("premium"))
        .alias("price_bucket"),

        pl.col("placed_at")
        .str.to_datetime("%Y-%m-%dT%H:%M:%SZ", strict=False)
        .dt.weekday()
        .is_in([5, 6])
        .alias("is_weekend"),

        pl.col("placed_at")
        .str.to_datetime("%Y-%m-%dT%H:%M:%SZ", strict=False)
        .dt.hour()
        .alias("hour_of_day"),

        (
                pl.col("delivered_at").str.to_datetime("%Y-%m-%dT%H:%M:%SZ", strict=False)
                - pl.col("placed_at").str.to_datetime("%Y-%m-%dT%H:%M:%SZ", strict=False)
        )
        .dt.total_days()
        .alias("days_to_deliver"),
    ])


def enrich_reviews(lf: pl.LazyFrame) -> pl.LazyFrame:
    total_votes = pl.col("helpful_votes") + pl.col("unhelpful_votes")
    return lf.with_columns([
        pl.when(pl.col("rating") >= 4).then(pl.lit("positive"))
        .when(pl.col("rating") == 3).then(pl.lit("neutral"))
        .otherwise(pl.lit("negative"))
        .alias("sentiment_bucket"),

        pl.when(total_votes > 0)
        .then(pl.col("helpful_votes").cast(pl.Float64) / total_votes.cast(pl.Float64))
        .otherwise(None)
        .alias("helpfulness_rate"),
    ])


def enrich_users(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.with_columns([
        pl.col("plan").is_in(["premium", "enterprise"]).alias("is_premium"),
    ])


def enrich_products(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.with_columns([
        (
                pl.col("dimensions_cm").struct.field("l")
                * pl.col("dimensions_cm").struct.field("w")
                * pl.col("dimensions_cm").struct.field("h")
        ).alias("volume_cm3"),

        (pl.col("stock") == 0).alias("is_out_of_stock"),

        pl.when(pl.col("price") < 30).then(pl.lit("budget"))
        .when(pl.col("price") < 150).then(pl.lit("mid"))
        .otherwise(pl.lit("premium"))
        .alias("price_tier"),
    ])


# ---------------------------------------------------------------------------
# Jointures
# ---------------------------------------------------------------------------

def join_orders_users(orders: pl.LazyFrame, users: pl.LazyFrame) -> pl.LazyFrame:
    users_slim = users.select([
        pl.col("user_id"),
        pl.col("email").alias("user_email"),
        pl.col("full_name").alias("user_full_name"),
        pl.col("plan").alias("user_plan"),
        pl.col("country").alias("user_country"),
        pl.col("is_verified").alias("user_is_verified"),
        pl.col("is_premium").alias("user_is_premium"),
    ])
    return orders.join(users_slim, on="user_id", how="left")


def join_reviews_products(reviews: pl.LazyFrame, products: pl.LazyFrame) -> pl.LazyFrame:
    products_slim = products.select([
        pl.col("product_id"),
        pl.col("name").alias("product_name"),
        pl.col("category").alias("product_category"),
        pl.col("subcategory").alias("product_subcategory"),
        pl.col("price").alias("product_price"),
        pl.col("price_tier").alias("product_price_tier"),
        pl.col("rating_avg").alias("product_rating_avg"),
    ])
    return reviews.join(products_slim, on="product_id", how="left")


def join_orders_reviews(orders: pl.LazyFrame, reviews: pl.LazyFrame) -> pl.LazyFrame:
    """
    Pour chaque order, agrège les métriques de reviews des produits commandés.
    On explose la liste items (structs) pour obtenir order_id x product_id,
    puis on joint les reviews agrégées par product_id.
    """
    # Polars lazy supporte explode — on extrait product_id depuis les structs
    order_items = (
        orders
        .select(["order_id", "dt", "items"])
        .explode("items")
        .with_columns(
            pl.col("items").struct.field("product_id").alias("product_id")
        )
        .select(["order_id", "product_id"])
    )

    review_agg = (
        reviews
        .group_by("product_id")
        .agg([
            pl.len().alias("nb_reviews"),
            pl.col("rating").mean().round(2).alias("avg_rating"),
            (
                    (pl.col("sentiment_bucket") == "positive").sum().cast(pl.Float64)
                    / pl.len().cast(pl.Float64)
            ).round(3).alias("pct_positive"),
        ])
    )

    order_review_agg = (
        order_items
        .join(review_agg, on="product_id", how="left")
        .group_by("order_id")
        .agg([
            pl.col("nb_reviews").sum().alias("total_reviews_on_items"),
            pl.col("avg_rating").mean().round(2).alias("avg_product_rating"),
            pl.col("pct_positive").mean().round(3).alias("avg_pct_positive"),
        ])
    )

    return orders.join(order_review_agg, on="order_id", how="left")


# ---------------------------------------------------------------------------
# Agrégations
# ---------------------------------------------------------------------------

def agg_revenue(orders: pl.LazyFrame) -> pl.LazyFrame:
    return (
        orders
        .with_columns(
            pl.col("shipping_address").struct.field("country").alias("shipping_country")
        )
        .group_by(["dt", "shipping_country", "currency"])
        .agg([
            pl.col("total_amount").sum().round(2).alias("revenue"),
            pl.col("total_amount").mean().round(2).alias("avg_order_value"),
            pl.len().alias("nb_orders"),
            pl.col("item_count").sum().alias("nb_items_sold"),
        ])
        .sort(["dt", "revenue"], descending=[False, True])
    )


def agg_order_status(orders: pl.LazyFrame) -> pl.LazyFrame:
    return (
        orders
        .group_by(["dt", "status"])
        .agg([
            pl.len().alias("nb_orders"),
            pl.col("total_amount").sum().round(2).alias("total_amount"),
            pl.col("days_to_deliver").mean().round(1).alias("avg_days_to_deliver"),
        ])
        .sort(["dt", "nb_orders"], descending=[False, True])
    )


def agg_product_rating(reviews: pl.LazyFrame) -> pl.LazyFrame:
    return (
        reviews
        .group_by(["dt", "product_id"])
        .agg([
            pl.col("rating").mean().round(2).alias("avg_rating"),
            pl.col("rating").std().round(3).alias("std_rating"),
            pl.len().alias("nb_reviews"),
            pl.col("verified_purchase").sum().alias("nb_verified"),
            (
                    pl.col("verified_purchase").sum().cast(pl.Float64)
                    / pl.len().cast(pl.Float64)
            ).round(3).alias("pct_verified"),
            (pl.col("rating") == 5).sum().alias("nb_5stars"),
            (pl.col("rating") == 1).sum().alias("nb_1star"),
        ])
        .sort("nb_reviews", descending=True)
    )


def agg_user_basket(orders: pl.LazyFrame) -> pl.LazyFrame:
    return (
        orders
        .filter(pl.col("status").is_in(["delivered", "shipped", "processing"]))
        .group_by(["dt", "user_id"])
        .agg([
            pl.col("total_amount").mean().round(2).alias("avg_basket"),
            pl.col("total_amount").sum().round(2).alias("total_spent"),
            pl.col("total_amount").max().round(2).alias("max_order"),
            pl.len().alias("nb_orders"),
            pl.col("item_count").mean().round(1).alias("avg_items_per_order"),
            pl.col("is_weekend").sum().alias("nb_weekend_orders"),
        ])
        .with_columns(
            pl.when(pl.col("total_spent") >= 1000).then(pl.lit("vip"))
            .when(pl.col("total_spent") >= 200).then(pl.lit("regular"))
            .otherwise(pl.lit("occasional"))
            .alias("customer_segment")
        )
    )


# ---------------------------------------------------------------------------
# Écriture Parquet partitionnée par dt
# ---------------------------------------------------------------------------

def write(lf: pl.LazyFrame, base: Path, name: str) -> None:
    dest = base / name
    dest.mkdir(parents=True, exist_ok=True)
    lf.sink_parquet(
        dest / "part-{dt}.parquet",
        compression="zstd",
        statistics=True,
        )
    print(f"  ✓ {name}")

# ---------------------------------------------------------------------------
# CLI + pipeline principal
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="DynamoDB NDJSON → Parquet (Polars)")
    p.add_argument("--input",  default="output",  help="Dossier source")
    p.add_argument("--output", default="parquet", help="Dossier destination")
    return p.parse_args()


def main() -> None:
    args   = parse_args()
    source = Path(args.input)
    output = Path(args.output)

    print(f"\nScan : {source}/dt=*/data.ndjson")
    lf = scan_all(source)

    # Split
    users    = enrich_users(split(lf, "USER"))
    products = enrich_products(split(lf, "PRODUCT"))
    orders   = enrich_orders(split(lf, "ORDER")).cache()
    reviews  = enrich_reviews(split(lf, "REVIEW")).cache()

    print(f"\nÉcriture dans {output}/\n")

    # Jointures
    write(join_orders_users(orders, users),          output, "orders_enriched")
    write(join_reviews_products(reviews, products),  output, "reviews_enriched")
    write(join_orders_reviews(orders, reviews),      output, "orders_reviews")

    # Agrégations
    write(agg_revenue(orders),          output, "agg_revenue")
    write(agg_order_status(orders),     output, "agg_order_status")
    write(agg_product_rating(reviews),  output, "agg_product_rating")
    write(agg_user_basket(orders),      output, "agg_user_basket")

    print("\nDone.")


if __name__ == "__main__":
    main()
