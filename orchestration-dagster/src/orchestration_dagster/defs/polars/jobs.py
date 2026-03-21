from dagster import define_asset_job
from .assets import github_commits_polars

polars_jobs = define_asset_job(
    name="polars_jobs",
    selection=[github_commits_polars],
)
