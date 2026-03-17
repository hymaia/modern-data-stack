import dagster as dg

@dg.asset
def daily_sales() -> None: ...


@dg.asset(deps=[daily_sales], group_name="sales")
def weekly_sales() -> None: ...


@dg.asset(
    deps=[weekly_sales],
    owners=["fcussac@hymaia.com"],
)
def weekly_sales_report(context: dg.AssetExecutionContext):
    context.log.info("Loading data for my_dataset")

