from dagster import define_asset_job
from .assets import polars_groupby_plain_data, polars_broadcastjoin_plain_data, polars_join_plain_data

polars_groupby_jobs = define_asset_job(
    name="polars_groupby_plain_data_jobs",
    selection=[polars_groupby_plain_data],
)

polars_broadcast_join_jobs = define_asset_job(
    name="polars_broadcastjoin_plain_data_jobs",
    selection=[polars_broadcastjoin_plain_data],
)

polars_join_jobs = define_asset_job(
    name="polars_join_plain_data_jobs",
    selection=[polars_join_plain_data],
)
