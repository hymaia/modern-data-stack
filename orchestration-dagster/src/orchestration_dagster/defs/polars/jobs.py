from dagster import define_asset_job
from .assets import polars_plain_data

polars_jobs = define_asset_job(
    name="polars_plain_data_jobs",
    selection=[polars_plain_data],
)
