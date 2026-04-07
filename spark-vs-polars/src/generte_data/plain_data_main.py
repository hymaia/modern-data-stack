import sys
from datetime import date, timedelta
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from pyspark.sql import functions as F
from pyspark.sql.types import *

# ── Args ─────────────────────────────────────────────────────────────────────
args = getResolvedOptions(
    sys.argv, ["JOB_NAME", "OUTPUT_PATH", "ROWS_PER_DATE", "START_DATE", "END_DATE"]
)

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

OUTPUT_PATH = args["OUTPUT_PATH"]
ROWS_PER_DATE = int(args["ROWS_PER_DATE"])
START_DATE = args[
    "START_DATE"
]  # "yyyy-mm-dd" — reste string, utilisé dans les expressions Spark
END_DATE = args["END_DATE"]

# ── Nombre de jours (seul calcul sur le driver, ultra léger) ─────────────────
n_days = (date.fromisoformat(END_DATE) - date.fromisoformat(START_DATE)).days + 1
total_rows = n_days * ROWS_PER_DATE

CANCELLATION_REASONS = ["out_of_stock", "user_request", "fraud", "payment_failed"]

# ── Génération 100% distribuée ────────────────────────────────────────────────
df = (
    spark.range(0, total_rows, numPartitions=2000)
    # dt : dérivée depuis l'index de la row
    .withColumn(
        "dt",
        F.date_add(
            F.lit(START_DATE).cast("date"), (F.col("id") / ROWS_PER_DATE).cast("int")
        ).cast("string"),
    )
    # placed_at : timestamp réaliste sur la journée
    .withColumn(
        "placed_at",
        F.concat(
            F.col("dt"),
            F.lit("T"),
            F.lpad((F.rand() * 23).cast("int").cast("string"), 2, "0"),
            F.lit(":"),
            F.lpad((F.rand() * 59).cast("int").cast("string"), 2, "0"),
            F.lit(":"),
            F.lpad((F.rand() * 59).cast("int").cast("string"), 2, "0"),
            F.lit("Z"),
        ),
    )
    .select(
        F.col("dt"),
        F.col("placed_at"),
        F.lpad((F.rand() * 999).cast("int").cast("string"), 3, "0").alias("store_id"),
        F.element_at(F.array(F.lit("FR"), F.lit("UK"), F.lit("DE"), F.lit("ES"), F.lit("IT")), (F.rand() * 5 + 1).cast("int")).alias("country"),
        F.element_at(F.array(F.lit("web"), F.lit("mobile"), F.lit("store"), F.lit("partner")), (F.rand() * 4 + 1).cast("int")).alias("channel"),
    )
)

# ── Écriture partitionnée par dt ──────────────────────────────────────────────
df.write.mode("overwrite").partitionBy("dt").json(OUTPUT_PATH)

print(f"✅ Done — {total_rows:,} records written to {OUTPUT_PATH}")
