from dagster import asset, OpExecutionContext
from dagster_k8s import PipesK8sClient

POLARS_IMAGE = "662195598891.dkr.ecr.eu-west-1.amazonaws.com/hymaia/spark-vs-polars:polars"
INPUT_FILE = "s3://hymaia-datalake-raw/spark-vs-polars/plain_data/10_000_000-rows"
INPUT_BROADCAST_JOIN_FILE = "s3://hymaia-datalake-raw/spark-vs-polars/cancellation_reason.json"
INPUT_JOIN_FILE = "s3://hymaia-datalake-raw/spark-vs-polars/join-example-dataset"
OUTPUT_GROUPBY_FILE = "s3://hymaia-datalake-staging/polars/plain_data/groupby/10_000_000-rows"
OUTPUT_BROADCAST_JOIN_FILE = "s3://hymaia-datalake-staging/polars/plain_data/broadcast_join/10_000_000-rows"
OUTPUT_JOIN_FILE = "s3://hymaia-datalake-staging/polars/plain_data/join/10_000_000-rows"


@asset
def polars_groupby_plain_data(context: OpExecutionContext, pipes_k8s_client: PipesK8sClient):
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
                    "name": "polars-groupby",
                    "image": POLARS_IMAGE,
                    "imagePullPolicy": "Always",
                    "args": ["src/spark_vs_polars/plain/groupby/polars_main.py"],
                    "env": [
                        {"name": "INPUT_FILE", "value": INPUT_FILE},
                        {"name": "INPUT_BROADCAST_JOIN_FILE", "value": INPUT_BROADCAST_JOIN_FILE},
                        {"name": "INPUT_JOIN_FILE", "value": INPUT_JOIN_FILE},
                        {"name": "OUTPUT_FILE", "value": OUTPUT_GROUPBY_FILE},
                    ],
                    "resources": {
                        "requests": {"cpu": "4000m", "memory": "8Gi"},
                        "limits": {"cpu": "4000m", "memory": "8Gi"},
                    },
                }
            ],
        },
    ).get_results()

@asset
def polars_broadcastjoin_plain_data(context: OpExecutionContext, pipes_k8s_client: PipesK8sClient):
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
                    "name": "polars-broadcast-join",
                    "image": POLARS_IMAGE,
                    "imagePullPolicy": "Always",
                    "args": ["src/spark_vs_polars/plain/broadcast_join/polars_main.py"],
                    "env": [
                        {"name": "INPUT_FILE", "value": INPUT_FILE},
                        {"name": "INPUT_BROADCAST_JOIN_FILE", "value": INPUT_BROADCAST_JOIN_FILE},
                        {"name": "INPUT_JOIN_FILE", "value": INPUT_JOIN_FILE},
                        {"name": "OUTPUT_FILE", "value": OUTPUT_BROADCAST_JOIN_FILE},
                    ],
                    "resources": {
                        "requests": {"cpu": "4000m", "memory": "8Gi"},
                        "limits": {"cpu": "4000m", "memory": "8Gi"},
                    },
                }
            ],
        },
    ).get_results()

@asset
def polars_join_plain_data(context: OpExecutionContext, pipes_k8s_client: PipesK8sClient):
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
                    "name": "polars-join",
                    "image": POLARS_IMAGE,
                    "imagePullPolicy": "Always",
                    "args": ["src/spark_vs_polars/plain/join/polars_main.py"],
                    "env": [
                        {"name": "INPUT_FILE", "value": INPUT_FILE},
                        {"name": "INPUT_BROADCAST_JOIN_FILE", "value": INPUT_BROADCAST_JOIN_FILE},
                        {"name": "INPUT_JOIN_FILE", "value": INPUT_JOIN_FILE},
                        {"name": "OUTPUT_FILE", "value": OUTPUT_JOIN_FILE},
                    ],
                    "resources": {
                        "requests": {"cpu": "4000m", "memory": "8Gi"},
                        "limits": {"cpu": "4000m", "memory": "8Gi"},
                    },
                }
            ],
        },
    ).get_results()
