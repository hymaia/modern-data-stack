from dagster import define_asset_job
from .assets import spark_plain_data

spark_jobs = define_asset_job(
    name="spark_plain_data_jobs",
    selection=[spark_plain_data],
)
