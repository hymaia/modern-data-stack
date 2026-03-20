from dagster import ScheduleDefinition
from .jobs import spark_jobs

github_commits_schedule = ScheduleDefinition(
    job=spark_jobs,
    cron_schedule="0 16 * * *",  # tous les jours à 6h UTC
)
