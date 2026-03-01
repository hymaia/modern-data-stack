import dagster as dg

from discover_dagster.defs.sales.assets import daily_sales, weekly_sales, weekly_sales_report

daily_job = dg.define_asset_job(
    name="daily_job",
    selection=dg.AssetSelection.assets(daily_sales),
)

weekly_job = dg.define_asset_job(
    name="weekly_job",
    selection=dg.AssetSelection.assets(weekly_sales, weekly_sales_report),
)
