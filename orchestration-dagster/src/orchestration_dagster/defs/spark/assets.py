from dagster import asset, OpExecutionContext
from spark.k8s import submit_spark_application, wait_for_spark_application, delete_spark_application

SPARK_IMAGE = "662195598891.dkr.ecr.eu-west-1.amazonaws.com/hymaia/spark-vs-polars"
INPUT_FILE = "s3a://hymaia-datalake-raw/commits/data"
OUTPUT_FILE = "s3a://hymaia-datalake-staging/spark-vs-polars/spark-outputs/commit"


@asset
def github_commits(context: OpExecutionContext):
    name = submit_spark_application(
        name="spark-vs-polars",
        image=SPARK_IMAGE,
        main_application_file="local:///app/src/spark_vs_polars/main.py",
        env={
            "INPUT_FILE": INPUT_FILE,
            "OUTPUT_FILE": OUTPUT_FILE,
        },
    )
    context.log.info(f"SparkApplication créée : {name}")

    try:
        final_state = wait_for_spark_application(name=name)
    finally:
        delete_spark_application(name=name)

    if final_state != "COMPLETED":
        raise Exception(f"Spark job {name} failed with state: {final_state}")
