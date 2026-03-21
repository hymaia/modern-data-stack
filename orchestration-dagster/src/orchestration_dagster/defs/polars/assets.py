from dagster import asset, OpExecutionContext
from dagster_k8s import PipesK8sClient

POLARS_IMAGE = "662195598891.dkr.ecr.eu-west-1.amazonaws.com/hymaia/spark-vs-polars:polars"
INPUT_FILE = "s3://hymaia-datalake-raw/commits/data/"
OUTPUT_FILE = "s3://hymaia-datalake-staging/polars-vs-spark/polars-outputs/commit"


@asset
def github_commits_polars(context: OpExecutionContext, pipes_k8s_client: PipesK8sClient):
    return pipes_k8s_client.run(
        context=context,
        namespace="polars",
        image=POLARS_IMAGE,
        base_pod_spec={
            "serviceAccountName": "polars-jobs",
            "containers": [
                {
                    "name": "polars",
                    "image": POLARS_IMAGE,
                    "imagePullPolicy": "Always",
                    "env": [
                        {"name": "INPUT_FILE", "value": INPUT_FILE},
                        {"name": "OUTPUT_FILE", "value": OUTPUT_FILE},
                    ],
                    "resources": {
                        "requests": {"cpu": "250m", "memory": "512Mi"},
                        "limits": {"cpu": "500m", "memory": "512Mi"},
                    },
                }
            ],
        },
    ).get_results()
