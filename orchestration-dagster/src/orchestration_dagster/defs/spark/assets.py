from dagster import asset, OpExecutionContext
from spark.k8s import submit_spark_application, wait_for_spark_application, delete_spark_application

SPARK_IMAGE = "662195598891.dkr.ecr.eu-west-1.amazonaws.com/hymaia/spark-vs-polars:spark"
INPUT_FILE = "s3a://hymaia-datalake-raw/spark-vs-polars/plain_data/10_000_000-rows"
INPUT_BROADCAST_JOIN_FILE = "s3a://hymaia-datalake-raw/spark-vs-polars/cancellation_reason.json"
INPUT_JOIN_FILE = "s3a://hymaia-datalake-raw/spark-vs-polars/join-example-dataset"
OUTPUT_GROUPBY_FILE = "s3a://hymaia-datalake-staging/spark/plain_data/groupby/10_000_000-rows"
OUTPUT_BROADCAST_JOIN_FILE = "s3a://hymaia-datalake-staging/spark/plain_data/broadcast_join/10_000_000-rows"
OUTPUT_JOIN_FILE = "s3a://hymaia-datalake-staging/spark/plain_data/join/10_000_000-rows"


@asset
def spark_groupby_plain_data(context: OpExecutionContext):
    name = submit_spark_application(
        name="spark-vs-polars-groupby",
        image=SPARK_IMAGE,
        main_application_file="local:///app/src/spark_vs_polars/plain/groupby/spark_main.py",
        env={
            "INPUT_FILE": INPUT_FILE,
            "INPUT_JOIN_FILE": INPUT_JOIN_FILE,
            "INPUT_BROADCAST_JOIN_FILE": INPUT_BROADCAST_JOIN_FILE,
            "OUTPUT_FILE": OUTPUT_GROUPBY_FILE,
        },
        executor_instances=3,
        driver_cores=1,
        driver_memory="2g",
        executor_cores=1,
        executor_memory="2g",
    )
    context.log.info(f"SparkApplication créée : {name}")

    try:
        final_state = wait_for_spark_application(name=name)
    finally:
        delete_spark_application(name=name)

    if final_state != "COMPLETED":
        raise Exception(f"Spark job {name} failed with state: {final_state}")

@asset
def spark_broadcastjoin_plain_data(context: OpExecutionContext):
    name = submit_spark_application(
        name="spark-vs-polars-broadcast-join",
        image=SPARK_IMAGE,
        main_application_file="local:///app/src/spark_vs_polars/plain/broadcast_join/spark_main.py",
        env={
            "INPUT_FILE": INPUT_FILE,
            "INPUT_JOIN_FILE": INPUT_JOIN_FILE,
            "INPUT_BROADCAST_JOIN_FILE": INPUT_BROADCAST_JOIN_FILE,
            "OUTPUT_FILE": OUTPUT_BROADCAST_JOIN_FILE,
        },
        executor_instances=3,
        driver_cores=1,
        driver_memory="2g",
        executor_cores=1,
        executor_memory="2g",
    )
    context.log.info(f"SparkApplication créée : {name}")

    try:
        final_state = wait_for_spark_application(name=name)
    finally:
        delete_spark_application(name=name)

    if final_state != "COMPLETED":
        raise Exception(f"Spark job {name} failed with state: {final_state}")

@asset
def spark_join_plain_data(context: OpExecutionContext):
    name = submit_spark_application(
        name="spark-vs-polars-join",
        image=SPARK_IMAGE,
        main_application_file="local:///app/src/spark_vs_polars/plain/join/spark_main.py",
        env={
            "INPUT_FILE": INPUT_FILE,
            "INPUT_JOIN_FILE": INPUT_JOIN_FILE,
            "INPUT_BROADCAST_JOIN_FILE": INPUT_BROADCAST_JOIN_FILE,
            "OUTPUT_FILE": OUTPUT_JOIN_FILE,
        },
        executor_instances=3,
        driver_cores=1,
        driver_memory="2g",
        executor_cores=1,
        executor_memory="2g",
    )
    context.log.info(f"SparkApplication créée : {name}")

    try:
        final_state = wait_for_spark_application(name=name)
    finally:
        delete_spark_application(name=name)

    if final_state != "COMPLETED":
        raise Exception(f"Spark job {name} failed with state: {final_state}")
