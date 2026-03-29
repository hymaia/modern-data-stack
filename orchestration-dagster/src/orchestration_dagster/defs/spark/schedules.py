from dagster import ScheduleDefinition
from .jobs import spark_jobs

spark_jobs_schedule = ScheduleDefinition(
    job=spark_jobs,
    cron_schedule="0 16 * * *",  # tous les jours à 6h UTC
)
