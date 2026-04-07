from dagster import define_asset_job
from .assets import spark_groupby_plain_data, spark_broadcastjoin_plain_data, spark_join_plain_data

spark_groupby_jobs = define_asset_job(
    name="spark_groupby_plain_data_jobs",
    selection=[spark_groupby_plain_data],
)

spark_broadcast_join_jobs = define_asset_job(
    name="spark_broadcastjoin_plain_data_jobs",
    selection=[spark_broadcastjoin_plain_data],
)

spark_join_jobs = define_asset_job(
    name="spark_join_plain_data_jobs",
    selection=[spark_join_plain_data],
)
