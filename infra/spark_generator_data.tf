resource "aws_s3_object" "glue_script" {
  bucket = aws_s3_bucket.raw.id
  key    = "glue-scripts/fake_orders_generator.py"
  source = "${path.module}/templates/fake_orders_generator.py"
  etag   = filemd5("${path.module}/templates/fake_orders_generator.py")
}

# ── IAM Role ─────────────────────────────────────────────────────────────────
resource "aws_iam_role" "glue_fake_orders" {
  name = "glue-fake-orders-generator"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "glue.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "glue_service" {
  role       = aws_iam_role.glue_fake_orders.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_access" {
  name = "glue-fake-orders-s3"
  role = aws_iam_role.glue_fake_orders.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "WriteData"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation",
          "s3:ListMultipartUploadParts",
        ]
        Resource = [
          aws_s3_bucket.raw.arn,
          "${aws_s3_bucket.raw.arn}/*",
        ]
      }
    ]
  })
}

# ── Glue Job ─────────────────────────────────────────────────────────────────
resource "aws_glue_job" "fake_orders_generator" {
  name         = "fake-orders-generator"
  role_arn     = aws_iam_role.glue_fake_orders.arn
  glue_version = "4.0"
  worker_type  = "G.2X"
  number_of_workers = 5

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.raw.id}/glue-scripts/fake_orders_generator.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"        = "python"
    "--job-bookmark-option" = "job-bookmark-disable"
    "--enable-metrics"      = "true"
    "--enable-continuous-cloudwatch-log" = "false"
    "--OUTPUT_PATH"         = "s3://${aws_s3_bucket.raw.id}/spark-vs-polars/plain_data/10_000_000_000-rows/"
    "--ROWS_PER_DATE"       = "9132420"
    "--START_DATE"          = "2023-01-01"
    "--END_DATE"            = "2025-12-31"
  }

  execution_property {
    max_concurrent_runs = 1
  }

  tags = {
    Purpose = "fake-data-generation"
  }
}
