from dagster import define_asset_job
from .assets import github_commits

spark_jobs = define_asset_job(
    name="spark_jobs",
    selection=[github_commits],
)
