from pathlib import Path
from dagster_dbt import DbtProject

DBT_PROJECT_DIR = Path(__file__).parent.parent

dbt_project = DbtProject(
    project_dir=DBT_PROJECT_DIR,
)

dbt_project.prepare_if_dev()
