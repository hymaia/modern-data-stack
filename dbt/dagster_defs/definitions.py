from dagster import Definitions, ScheduleDefinition, define_asset_job
from dagster_dbt import DbtCliResource

from .assets.dbt import my_dbt_assets
from .project import dbt_project

daily_schedule = ScheduleDefinition(
    job=define_asset_job("dbt_daily_job", selection="*"),
    cron_schedule="0 6 * * *",  # tous les jours à 6h UTC
)

defs = Definitions(
    assets=[my_dbt_assets],
    schedules=[daily_schedule],
    resources={
        "dbt": DbtCliResource(project_dir=dbt_project),
    },
)
