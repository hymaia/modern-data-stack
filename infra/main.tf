resource "local_file" "dagster_values" {
  filename = "${path.module}/../apps/dagster/values.yaml"
  content  = templatefile("${path.module}/templates/dagster-values.yaml.tpl", {
    certificate_arn = data.aws_acm_certificate.fcussac_app.arn
    rds_endpoint    = aws_rds_cluster_instance.dagster.endpoint
    ecr_user_code   = aws_ecr_repository.dagster_user_code.repository_url
    dagster_user_code_github_dbt = aws_ecr_repository.dagster_user_code_github_dbt.repository_url
    role_iam_dagster             = aws_iam_role.dagster_code_location.arn
    role_iam_polars              = aws_iam_role.polars_jobs.arn
  })
}

resource "local_file" "airbyte_values" {
  filename = "${path.module}/../apps/airbyte/values.yaml"
  content  = templatefile("${path.module}/templates/airbyte-values.yaml.tpl", {
    certificate_arn = data.aws_acm_certificate.fcussac_app.arn
    rds_endpoint    = aws_rds_cluster_instance.airbyte.endpoint
    role_iam_arn    = aws_iam_role.airbyte_s3.arn
  })
}

resource "local_file" "metabase_values" {
  filename = "${path.module}/../apps/metabase/values.yaml"
  content  = templatefile("${path.module}/templates/metabase-values.yaml.tpl", {
    certificate_arn = data.aws_acm_certificate.fcussac_app.arn
    rds_endpoint    = aws_rds_cluster_instance.metabase.endpoint
    role_iam_arn    = aws_iam_role.metabase.arn
  })
}

resource "local_file" "spark_operator_values" {
  filename = "${path.module}/../apps/spark/values.yaml"
  content  = templatefile("${path.module}/templates/spark-operator-values.yaml.tpl", {
    role_iam_arn = aws_iam_role.spark_jobs.arn
  })
}
