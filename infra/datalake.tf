resource "aws_s3_bucket" "raw" {
  bucket = "hymaia-datalake-raw"

  tags = {
    Name        = "Raw Data Bucket"
    Layer       = "raw"
  }
}

resource "aws_s3_bucket" "staging" {
  bucket = "hymaia-datalake-staging"

  tags = {
    Name        = "Staging Data Bucket"
    Layer       = "staging"
  }
}

resource "aws_s3_bucket" "mart" {
  bucket = "hymaia-datalake-mart"

  tags = {
    Name        = "Mart Data Bucket"
    Layer       = "mart"
  }
}

# Versioning pour les buckets
resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "staging" {
  bucket = aws_s3_bucket.staging.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_versioning" "mart" {
  bucket = aws_s3_bucket.mart.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Encryption pour les buckets
resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "staging" {
  bucket = aws_s3_bucket.staging.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mart" {
  bucket = aws_s3_bucket.mart.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Bloquer l'accès public
resource "aws_s3_bucket_public_access_block" "raw" {
  bucket = aws_s3_bucket.raw.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "staging" {
  bucket = aws_s3_bucket.staging.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "mart" {
  bucket = aws_s3_bucket.mart.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Bucket pour les résultats Athena
resource "aws_s3_bucket" "athena_results" {
  bucket = "raw-athena-results"

  tags = {
    Name        = "Athena Query Results"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "athena_results" {
  bucket = aws_s3_bucket.athena_results.id

  rule {
    id     = "delete-old-results"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 30
    }
  }
}

# Glue Catalog Database pour chaque couche
resource "aws_glue_catalog_database" "raw" {
  name        = "hymaia_datalake_raw"
  description = "Raw data layer - données brutes sources"

  location_uri = "s3://${aws_s3_bucket.raw.bucket}/"
}

resource "aws_glue_catalog_database" "staging" {
  name        = "hymaia_datalake_staging"
  description = "Staging layer - données nettoyées et transformées"

  location_uri = "s3://${aws_s3_bucket.staging.bucket}/"
}

resource "aws_glue_catalog_database" "mart" {
  name        = "hymaia_datalake_mart"
  description = "Mart layer - données agrégées et prêtes pour la consommation"

  location_uri = "s3://${aws_s3_bucket.mart.bucket}/"
}

# Athena Workgroup
resource "aws_athena_workgroup" "main" {
  name        = "hymaia-datalake-workgroup"
  description = "Workgroup principal pour les requêtes Athena"

  configuration {
    enforce_workgroup_configuration    = false
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_results.bucket}/output/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }
  }

  tags = {
    Name        = "Main Athena Workgroup"
  }
}

# IAM Role pour Athena
resource "aws_iam_role" "athena_user_role" {
  name = "hymaia-datalake-athena-user-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "athena.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "Athena User Role"
  }
}

# IAM Policy pour Athena
resource "aws_iam_role_policy" "athena_policy" {
  name = "hymaia-datalake-athena-policy"
  role = aws_iam_role.athena_user_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:ListMultipartUploadParts",
          "s3:AbortMultipartUpload",
          "s3:PutObject"
        ]
        Resource = [
          aws_s3_bucket.raw.arn,
          "${aws_s3_bucket.raw.arn}/*",
          aws_s3_bucket.staging.arn,
          "${aws_s3_bucket.staging.arn}/*",
          aws_s3_bucket.mart.arn,
          "${aws_s3_bucket.mart.arn}/*",
          aws_s3_bucket.athena_results.arn,
          "${aws_s3_bucket.athena_results.arn}/*"
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
          "glue:BatchGetPartition",
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable"
        ]
        Resource = [
          "arn:aws:glue:*:*:catalog",
          "arn:aws:glue:*:*:database/${aws_glue_catalog_database.raw.name}",
          "arn:aws:glue:*:*:database/${aws_glue_catalog_database.staging.name}",
          "arn:aws:glue:*:*:database/${aws_glue_catalog_database.mart.name}",
          "arn:aws:glue:*:*:table/${aws_glue_catalog_database.raw.name}/*",
          "arn:aws:glue:*:*:table/${aws_glue_catalog_database.staging.name}/*",
          "arn:aws:glue:*:*:table/${aws_glue_catalog_database.mart.name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution",
          "athena:GetWorkGroup"
        ]
        Resource = [
          aws_athena_workgroup.main.arn
        ]
      }
    ]
  })
}
