from dagster import asset, OpExecutionContext
from spark.k8s import submit_spark_application, wait_for_spark_application, delete_spark_application

SPARK_IMAGE = "662195598891.dkr.ecr.eu-west-1.amazonaws.com/hymaia/spark-vs-polars:spark"
INPUT_FILE = "s3a://hymaia-datalake-raw/spark-vs-polars/plain_data/1_000_000_000-rows"
OUTPUT_FILE = "s3a://hymaia-datalake-staging/spark/plain_data/1_000_000_000-rows"


@asset
def spark_plain_data(context: OpExecutionContext):
    name = submit_spark_application(
        name="spark-vs-polars",
        image=SPARK_IMAGE,
        main_application_file="local:///app/src/spark_vs_polars/plain/spark_main.py",
        env={
            "INPUT_FILE": INPUT_FILE,
            "OUTPUT_FILE": OUTPUT_FILE,
        },
        executor_instances=5,
        driver_cores=2,
        driver_memory="4g",
        executor_cores=2,
        executor_memory="4g",
    )
    context.log.info(f"SparkApplication créée : {name}")

    try:
        final_state = wait_for_spark_application(name=name)
    finally:
        delete_spark_application(name=name)

    if final_state != "COMPLETED":
        raise Exception(f"Spark job {name} failed with state: {final_state}")
