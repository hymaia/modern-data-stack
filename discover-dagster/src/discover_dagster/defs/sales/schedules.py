import dagster as dg

from discover_dagster.defs.sales.jobs import weekly_job, daily_job

daily_schedule = dg.ScheduleDefinition(
    job=daily_job,
    cron_schedule="0 8 * * *",  # tous les jours à 8h
)

weekly_schedule = dg.ScheduleDefinition(
    job=weekly_job,
    cron_schedule="0 8 * * 1",  # tous les lundis à 8h
)
