"""
transform_dynamo_spark.py
=========================
Lit les fichiers NDJSON partitionnés (output/dt=YYYY-MM-DD/data.ndjson)
via les primitives natives Spark, applique les transformations et écrit
en Parquet partitionné par dt.

Usage:
    pip install pyspark
    python transform_dynamo_spark.py --input output --output parquet_spark
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

def get_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("transform_dynamo")
        .master("local[*]")
        .config("spark.driver.memory", "24g")
        .getOrCreate()
    )


# ---------------------------------------------------------------------------
# Lecture native Spark
# ---------------------------------------------------------------------------

def scan_all(spark: SparkSession, source: Path) -> DataFrame:
    """
    Spark lit récursivement tous les JSON sous source/,
    injecte automatiquement la colonne dt via le hive partitioning.
    Le schéma est inféré sur l'ensemble des fichiers en un seul scan.
    """
    return (
        spark.read.json(str(source))
    )


# ---------------------------------------------------------------------------
# Split par entity_type
# ---------------------------------------------------------------------------

def split(df: DataFrame, entity_type: str) -> DataFrame:
    return df.filter(F.col("entity_type") == entity_type)


# ---------------------------------------------------------------------------
# Enrichissements
# ---------------------------------------------------------------------------

def enrich_orders(df: DataFrame) -> DataFrame:
    placed    = F.to_timestamp("placed_at",    "yyyy-MM-dd'T'HH:mm:ss'Z'")
    delivered = F.to_timestamp("delivered_at", "yyyy-MM-dd'T'HH:mm:ss'Z'")
    return (
        df
        .withColumn("price_bucket",
                    F.when(F.col("total_amount") < 50,  F.lit("low"))
                    .when(F.col("total_amount") < 200, F.lit("mid"))
                    .when(F.col("total_amount") < 500, F.lit("high"))
                    .otherwise(F.lit("premium"))
                    )
        .withColumn("is_weekend",
                    F.dayofweek(placed).isin([1, 7])
                    )
        .withColumn("hour_of_day", F.hour(placed))
        .withColumn("days_to_deliver",
                    F.when(delivered.isNotNull(), F.datediff(delivered, placed))
                    .otherwise(F.lit(None).cast("int"))
                    )
    )


def enrich_reviews(df: DataFrame) -> DataFrame:
    total_votes = F.col("helpful_votes") + F.col("unhelpful_votes")
    return (
        df
        .withColumn("sentiment_bucket",
                    F.when(F.col("rating") >= 4, F.lit("positive"))
                    .when(F.col("rating") == 3, F.lit("neutral"))
                    .otherwise(F.lit("negative"))
                    )
        .withColumn("helpfulness_rate",
                    F.when(
                        total_votes > 0,
                        F.col("helpful_votes").cast("double") / total_votes.cast("double")
                    ).otherwise(F.lit(None).cast("double"))
                    )
    )


def enrich_users(df: DataFrame) -> DataFrame:
    return df.withColumn(
        "is_premium",
        F.col("plan").isin(["premium", "enterprise"])
    )


def enrich_products(df: DataFrame) -> DataFrame:
    return (
        df
        .withColumn("volume_cm3",
                    F.col("dimensions_cm.l")
                    * F.col("dimensions_cm.w")
                    * F.col("dimensions_cm.h")
                    )
        .withColumn("is_out_of_stock", F.col("stock") == 0)
        .withColumn("price_tier",
                    F.when(F.col("price") < 30,  F.lit("budget"))
                    .when(F.col("price") < 150, F.lit("mid"))
                    .otherwise(F.lit("premium"))
                    )
    )


# ---------------------------------------------------------------------------
# Jointures
# ---------------------------------------------------------------------------

def join_orders_users(orders: DataFrame, users: DataFrame) -> DataFrame:
    users_slim = users.select(
        F.col("user_id"),
        F.col("email").alias("user_email"),
        F.col("full_name").alias("user_full_name"),
        F.col("plan").alias("user_plan"),
        F.col("country").alias("user_country"),
        F.col("is_verified").alias("user_is_verified"),
        F.col("is_premium").alias("user_is_premium"),
    )
    return orders.join(users_slim, on="user_id", how="left")


def join_reviews_products(reviews: DataFrame, products: DataFrame) -> DataFrame:
    products_slim = products.select(
        F.col("product_id"),
        F.col("name").alias("product_name"),
        F.col("category").alias("product_category"),
        F.col("subcategory").alias("product_subcategory"),
        F.col("price").alias("product_price"),
        F.col("price_tier").alias("product_price_tier"),
        F.col("rating_avg").alias("product_rating_avg"),
    )
    return reviews.join(products_slim, on="product_id", how="left")


def join_orders_reviews(orders: DataFrame, reviews: DataFrame) -> DataFrame:
    order_items = (
        orders
        .select("order_id", F.explode("items").alias("item"))
        .select("order_id", F.col("item.product_id").alias("product_id"))
    )

    review_agg = (
        reviews
        .groupBy("product_id")
        .agg(
            F.count("*").alias("nb_reviews"),
            F.round(F.mean("rating"), 2).alias("avg_rating"),
            F.round(
                F.sum((F.col("sentiment_bucket") == "positive").cast("double"))
                / F.count("*").cast("double"),
                3
            ).alias("pct_positive"),
        )
    )

    order_review_agg = (
        order_items
        .join(review_agg, on="product_id", how="left")
        .groupBy("order_id")
        .agg(
            F.sum("nb_reviews").alias("total_reviews_on_items"),
            F.round(F.mean("avg_rating"), 2).alias("avg_product_rating"),
            F.round(F.mean("pct_positive"), 3).alias("avg_pct_positive"),
        )
    )

    return orders.join(order_review_agg, on="order_id", how="left")


# ---------------------------------------------------------------------------
# Agrégations
# ---------------------------------------------------------------------------

def agg_revenue(orders: DataFrame) -> DataFrame:
    return (
        orders
        .withColumn("shipping_country", F.col("shipping_address.country"))
        .groupBy("dt", "shipping_country", "currency")
        .agg(
            F.round(F.sum("total_amount"), 2).alias("revenue"),
            F.round(F.mean("total_amount"), 2).alias("avg_order_value"),
            F.count("*").alias("nb_orders"),
            F.sum("item_count").alias("nb_items_sold"),
        )
        .orderBy("dt", F.desc("revenue"))
    )


def agg_order_status(orders: DataFrame) -> DataFrame:
    return (
        orders
        .groupBy("dt", "status")
        .agg(
            F.count("*").alias("nb_orders"),
            F.round(F.sum("total_amount"), 2).alias("total_amount"),
            F.round(F.mean("days_to_deliver"), 1).alias("avg_days_to_deliver"),
        )
        .orderBy("dt", F.desc("nb_orders"))
    )


def agg_product_rating(reviews: DataFrame) -> DataFrame:
    return (
        reviews
        .groupBy("dt", "product_id")
        .agg(
            F.round(F.mean("rating"), 2).alias("avg_rating"),
            F.round(F.stddev("rating"), 3).alias("std_rating"),
            F.count("*").alias("nb_reviews"),
            F.sum(F.col("verified_purchase").cast("int")).alias("nb_verified"),
            F.round(
                F.sum(F.col("verified_purchase").cast("double"))
                / F.count("*").cast("double"),
                3
            ).alias("pct_verified"),
            F.sum((F.col("rating") == 5).cast("int")).alias("nb_5stars"),
            F.sum((F.col("rating") == 1).cast("int")).alias("nb_1star"),
        )
        .orderBy(F.desc("nb_reviews"))
    )


def agg_user_basket(orders: DataFrame) -> DataFrame:
    return (
        orders
        .filter(F.col("status").isin(["delivered", "shipped", "processing"]))
        .groupBy("dt", "user_id")
        .agg(
            F.round(F.mean("total_amount"), 2).alias("avg_basket"),
            F.round(F.sum("total_amount"), 2).alias("total_spent"),
            F.round(F.max("total_amount"), 2).alias("max_order"),
            F.count("*").alias("nb_orders"),
            F.round(F.mean("item_count"), 1).alias("avg_items_per_order"),
            F.sum(F.col("is_weekend").cast("int")).alias("nb_weekend_orders"),
        )
        .withColumn("customer_segment",
                    F.when(F.col("total_spent") >= 1000, F.lit("vip"))
                    .when(F.col("total_spent") >= 200,  F.lit("regular"))
                    .otherwise(F.lit("occasional"))
                    )
    )


# ---------------------------------------------------------------------------
# Écriture Parquet partitionnée par dt
# ---------------------------------------------------------------------------

def write(df: DataFrame, base: Path, name: str) -> None:
    (
        df.write
        .mode("overwrite")
        .partitionBy("dt")
        .parquet(str(base / name))
    )
    print(f"  ✓ {name}")


# ---------------------------------------------------------------------------
# CLI + pipeline principal
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="DynamoDB NDJSON → Parquet (Spark)")
    p.add_argument("--input",  default="output",        help="Dossier source")
    p.add_argument("--output", default="parquet_spark", help="Dossier destination")
    return p.parse_args()


def main() -> None:
    args   = parse_args()
    source = Path(args.input)
    output = Path(args.output)

    spark = get_spark()
    spark.sparkContext.setLogLevel("WARN")

    print(f"\nScan : {source}/dt=*/data.ndjson")
    df = scan_all(spark, source)

    users    = enrich_users(split(df, "USER"))
    products = enrich_products(split(df, "PRODUCT"))
    orders   = enrich_orders(split(df, "ORDER"))
    reviews  = enrich_reviews(split(df, "REVIEW"))

    orders.cache()
    reviews.cache()

    print(f"\nÉcriture dans {output}/\n")

    write(join_orders_users(orders, users),         output, "orders_enriched")
    write(join_reviews_products(reviews, products), output, "reviews_enriched")
    write(join_orders_reviews(orders, reviews),     output, "orders_reviews")
    write(agg_revenue(orders),                      output, "agg_revenue")
    write(agg_order_status(orders),                 output, "agg_order_status")
    write(agg_product_rating(reviews),              output, "agg_product_rating")
    write(agg_user_basket(orders),                  output, "agg_user_basket")

    print("\nDone.")


if __name__ == "__main__":
    main()
