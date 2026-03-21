from pathlib import Path

from dagster import definitions, load_from_defs_folder, Definitions
from dagster_k8s import PipesK8sClient


@definitions
def defs():
    loaded = load_from_defs_folder(path_within_project=Path(__file__).parent)
    return Definitions.merge(
        loaded,
        Definitions(
            resources={
                "pipes_k8s_client": PipesK8sClient(),
            }
        ),
    )
