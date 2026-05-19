resource "aws_iam_role" "nl_query_agent" {
  name               = "${local.prefix}-nl-query-agent-role"
  assume_role_policy = local.irsa_assume_policy["nl-query-agent"]
}

# ==============================================================
# Policy — Glue
# ==============================================================
data "aws_iam_policy_document" "glue" {
  statement {
    effect = "Allow"
    actions = [
      "glue:GetDatabase",
      "glue:GetDatabases",
      "glue:GetTable",
      "glue:GetTables",
      "glue:GetPartition",
      "glue:GetPartitions",
    ]
    resources = [
      "arn:aws:glue:eu-west-1:662195598891:catalog",
      aws_glue_catalog_database.raw.arn,
      "arn:aws:glue:eu-west-1:662195598891:table/${aws_glue_catalog_database.raw.name}/*",
    ]
  }
}

resource "aws_iam_policy" "glue" {
  name   = "${local.prefix}-glue-policy"
  policy = data.aws_iam_policy_document.glue.json
}

resource "aws_iam_role_policy_attachment" "glue" {
  role       = aws_iam_role.nl_query_agent.name
  policy_arn = aws_iam_policy.glue.arn
}

# ==============================================================
# Policy — Athena
# ==============================================================
data "aws_iam_policy_document" "athena" {
  statement {
    effect = "Allow"
    actions = [
      "athena:StartQueryExecution",
      "athena:GetQueryExecution",
      "athena:GetQueryResults",
      "athena:StopQueryExecution",
      "athena:ListQueryExecutions",
    ]
    resources = [aws_athena_workgroup.agent.arn]
  }
}

resource "aws_iam_policy" "athena" {
  name   = "${local.prefix}-athena-policy"
  policy = data.aws_iam_policy_document.athena.json
}

resource "aws_iam_role_policy_attachment" "athena" {
  role       = aws_iam_role.nl_query_agent.name
  policy_arn = aws_iam_policy.athena.arn
}

# ==============================================================
# Policy — S3 résultats Athena
# ==============================================================
data "aws_iam_policy_document" "s3" {
  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:ListBucket",
      "s3:GetBucketLocation",
    ]
    resources = [
      aws_s3_bucket.athena_results.arn,
      "${aws_s3_bucket.athena_results.arn}/*"
    ]
  }
}

resource "aws_iam_policy" "s3" {
  name   = "${local.prefix}-s3-policy"
  policy = data.aws_iam_policy_document.s3.json
}

resource "aws_iam_role_policy_attachment" "s3" {
  role       = aws_iam_role.nl_query_agent.name
  policy_arn = aws_iam_policy.s3.arn
}

# ==============================================================
# Outputs — à transmettre au projet nl-sql-agent
# ==============================================================
output "pod_iam_role_name" {
  description = "Nom du role IAM à renseigner dans data_platform_role_name du terraform nl-sql-agent"
  value       = aws_iam_role.nl_query_agent.name
}

output "pod_iam_role_arn" {
  description = "ARN du role IAM à renseigner dans values.yaml (serviceAccount.iamRoleArn)"
  value       = aws_iam_role.nl_query_agent.arn
}
