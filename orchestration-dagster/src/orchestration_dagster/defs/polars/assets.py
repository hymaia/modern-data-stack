from dagster import asset, OpExecutionContext
from dagster_k8s import PipesK8sClient

POLARS_IMAGE = "662195598891.dkr.ecr.eu-west-1.amazonaws.com/hymaia/spark-vs-polars:polars"
INPUT_FILE = "s3://hymaia-datalake-raw/spark-vs-polars/plain_data/1_000_000_000-rows"
OUTPUT_FILE = "s3://hymaia-datalake-staging/polars/plain_data/1_000_000_000-rows"


@asset
def polars_plain_data(context: OpExecutionContext, pipes_k8s_client: PipesK8sClient):
    return pipes_k8s_client.run(
        context=context,
        namespace="polars",
        image=POLARS_IMAGE,
        base_pod_spec={
            "serviceAccountName": "polars-jobs",
            "nodeSelector": {
                "node-role": "spark-worker"
            },
            "tolerations": [
                {
                    "key": "spark-vs-polars-worker",
                    "operator": "Equal",
                    "value": "true",
                    "effect": "NoSchedule",
                }
            ],
            "containers": [
                {
                    "name": "polars",
                    "image": POLARS_IMAGE,
                    "imagePullPolicy": "Always",
                    "args": ["src/spark_vs_polars/plain/polars_main.py"],
                    "env": [
                        {"name": "INPUT_FILE", "value": INPUT_FILE},
                        {"name": "OUTPUT_FILE", "value": OUTPUT_FILE},
                    ],
                    "resources": {
                        "requests": {"cpu": "12000m", "memory": "24Gi"},
                        "limits": {"cpu": "12000m", "memory": "24Gi"},
                    },
                }
            ],
        },
    ).get_results()
