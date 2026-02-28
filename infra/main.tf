resource "local_file" "dagster_values" {
  filename = "${path.module}/../apps/dagster/values.yaml"
  content  = templatefile("${path.module}/templates/dagster-values.yaml.tpl", {
    certificate_arn = data.aws_acm_certificate.fcussac_app.arn
    rds_endpoint    = aws_rds_cluster_instance.dagster.endpoint
  })
}
