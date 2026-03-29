import uuid
import time
from kubernetes import client, config


def submit_spark_application(
        name: str,
        image: str,
        main_application_file: str,
        env: dict[str, str],
        namespace: str = "spark",
        service_account: str = "spark-jobs",
        spark_version: str = "4.1.1",
        driver_cores: int = 1,
        driver_memory: str = "512m",
        executor_cores: int = 1,
        executor_memory: str = "512m",
        executor_instances: int = 3,
        spark_conf: dict[str, str] | None = None,
        node_selector: dict[str, str] | None = None,
) -> str:
    config.load_incluster_config()

    unique_name = f"{name}-{uuid.uuid4().hex[:8]}"

    default_spark_conf = {
        "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3a.aws.credentials.provider": "software.amazon.awssdk.auth.credentials.WebIdentityTokenFileCredentialsProvider",
    }

    k8s_env = [{"name": k, "value": v} for k, v in env.items()]
    default_node_selector = {"node-role": "spark-worker"}
    resolved_node_selector = {**default_node_selector, **(node_selector or {})}

    tolerations = [
        {
            "key": "spark-vs-polars-worker",
            "operator": "Equal",
            "value": "true",
            "effect": "NoSchedule",
        }
    ]

    spark_app = {
        "apiVersion": "sparkoperator.k8s.io/v1beta2",
        "kind": "SparkApplication",
        "metadata": {
            "name": unique_name,
            "namespace": namespace,
        },
        "spec": {
            "type": "Python",
            "pythonVersion": "3",
            "mode": "cluster",
            "image": image,
            "imagePullPolicy": "Always",
            "mainApplicationFile": main_application_file,
            "sparkVersion": spark_version,
            "sparkConf": {**default_spark_conf, **(spark_conf or {})},
            "driver": {
                "cores": driver_cores,
                "memory": driver_memory,
                "serviceAccount": service_account,
                "env": k8s_env,
                "nodeSelector": resolved_node_selector,
                "tolerations": tolerations,
            },
            "executor": {
                "cores": executor_cores,
                "instances": executor_instances,
                "memory": executor_memory,
                "env": k8s_env,
                "nodeSelector": resolved_node_selector,
                "tolerations": tolerations,
            },
            "restartPolicy": {"type": "Never"},
        },
    }

    client.CustomObjectsApi().create_namespaced_custom_object(
        group="sparkoperator.k8s.io",
        version="v1beta2",
        namespace=namespace,
        plural="sparkapplications",
        body=spark_app,
    )

    return unique_name


def wait_for_spark_application(
        name: str,
        namespace: str = "spark",
        poll_interval: int = 10,
        timeout: int = 36000,
) -> str:
    config.load_incluster_config()
    crd_api = client.CustomObjectsApi()

    terminal_states = {"COMPLETED", "FAILED", "SUBMISSION_FAILED", "INVALIDATING"}
    elapsed = 0

    while elapsed < timeout:
        app = crd_api.get_namespaced_custom_object(
            group="sparkoperator.k8s.io",
            version="v1beta2",
            namespace=namespace,
            plural="sparkapplications",
            name=name,
        )
        state = app.get("status", {}).get("applicationState", {}).get("state", "UNKNOWN")
        if state in terminal_states:
            return state

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError(f"SparkApplication {name} did not complete within {timeout}s")


def delete_spark_application(name: str, namespace: str = "spark") -> None:
    config.load_incluster_config()
    client.CustomObjectsApi().delete_namespaced_custom_object(
        group="sparkoperator.k8s.io",
        version="v1beta2",
        namespace=namespace,
        plural="sparkapplications",
        name=name,
    )
