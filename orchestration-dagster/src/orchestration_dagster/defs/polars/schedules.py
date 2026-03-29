from dagster import ScheduleDefinition
from .jobs import polars_jobs

polars_jobs_schedule = ScheduleDefinition(
    job=polars_jobs,
    cron_schedule="0 16 * * *",  # tous les jours à 6h UTC
)
