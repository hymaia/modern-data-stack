resource "aws_iam_role" "spark_jobs" {
  name               = "${local.prefix}-spark-jobs"
  assume_role_policy = local.irsa_assume_policy["spark-jobs"]
}

resource "aws_iam_role" "polars_jobs" {
  name               = "${local.prefix}-polars-jobs"
  assume_role_policy = local.irsa_assume_policy["polars-jobs"]
}

resource "aws_iam_policy" "data_jobs" {
  name = "${local.prefix}-data-jobs"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation",
        ]
        Resource = [
          aws_s3_bucket.raw.arn,
          "${aws_s3_bucket.raw.arn}/*",
          aws_s3_bucket.staging.arn,
          "${aws_s3_bucket.staging.arn}/*",
          aws_s3_bucket.mart.arn,
          "${aws_s3_bucket.mart.arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable",
          "glue:BatchCreatePartition",
          "glue:BatchDeletePartition",
        ]
        Resource = [
          "arn:aws:glue:eu-west-1:662195598891:catalog",
          "arn:aws:glue:eu-west-1:662195598891:database/*",
          "arn:aws:glue:eu-west-1:662195598891:table/*/*",
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "spark_jobs" {
  role       = aws_iam_role.spark_jobs.name
  policy_arn = aws_iam_policy.data_jobs.arn
}

resource "aws_iam_role_policy_attachment" "polars_jobs" {
  role       = aws_iam_role.polars_jobs.name
  policy_arn = aws_iam_policy.data_jobs.arn
}

resource "kubernetes_namespace_v1" "spark" {
  metadata {
    name = "spark"
  }
}

resource "aws_ecr_repository" "spark_vs_polars" {
  name = "hymaia/spark-vs-polars"
  image_tag_mutability = "MUTABLE"
  force_delete = true
}
