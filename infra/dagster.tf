resource "aws_rds_cluster" "dagster" {
  cluster_identifier  = "dagster"
  engine              = "aurora-postgresql"
  engine_mode         = "provisioned"
  engine_version      = "16.4"
  database_name       = "dagster"
  master_username     = "dagster"
  master_password     = random_password.dagster_db.result

  db_subnet_group_name   = local.subnet_group_name
  vpc_security_group_ids = [aws_security_group.dagster_db.id]

  skip_final_snapshot = true
  deletion_protection = false
  backup_retention_period = 1

  serverlessv2_scaling_configuration {
    min_capacity = 0.0
    max_capacity = 2.0
    seconds_until_auto_pause = 360
  }

  tags = {
    Name = "dagster"
  }
}

resource "aws_rds_cluster_instance" "dagster" {
  identifier         = "dagster"
  cluster_identifier = aws_rds_cluster.dagster.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.dagster.engine
  engine_version     = aws_rds_cluster.dagster.engine_version

  db_subnet_group_name = local.subnet_group_name
}

resource "aws_security_group" "dagster_db" {
  name   = "dagster-db"
  vpc_id = local.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.kubernetes.cluster[0].cluster_primary_security_group_id]
  }
}

resource "random_password" "dagster_db" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "dagster_db" {
  name = "dagster/postgresql"
}

resource "aws_secretsmanager_secret_version" "dagster_db" {
  secret_id = aws_secretsmanager_secret.dagster_db.id
  secret_string = jsonencode({
    password = random_password.dagster_db.result
  })
}

resource "aws_iam_role" "dagster_code_location" {
  name               = "${local.prefix}-dagster-code-location-role"
  assume_role_policy = local.irsa_assume_policy["dagster-code-location-role"]
}

resource "aws_iam_role_policy" "dagster_athena" {
  name = "dagster-athena-policy"
  role = aws_iam_role.dagster_code_location.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [

      # Athena - exécution des queries
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:StopQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:GetQueryResultsStream",
          "athena:ListQueryExecutions",
          "athena:GetWorkGroup",
          "athena:ListWorkGroups",
          "athena:BatchGetQueryExecution"
        ]
        Resource = [
          aws_athena_workgroup.main.arn
        ]
      },

      # Glue - lecture du catalogue
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
          "glue:GetTableVersion",
          "glue:GetTableVersions",
          "glue:BatchDeleteTableVersion",
        ]
        Resource = [
          "arn:aws:glue:eu-west-1:662195598891:catalog",
          "arn:aws:glue:eu-west-1:662195598891:database/*",
          "arn:aws:glue:eu-west-1:662195598891:table/*/*",
        ]
      },

      # Glue - écriture (dbt crée/modifie des tables)
      {
        Effect = "Allow"
        Action = [
          "glue:CreateTable",
          "glue:UpdateTable",
          "glue:DeleteTable",
          "glue:CreatePartition",
          "glue:UpdatePartition",
          "glue:DeletePartition",
          "glue:BatchCreatePartition",
          "glue:BatchDeletePartition"
        ]
        Resource = [
          "arn:aws:glue:eu-west-1:662195598891:catalog",
          "arn:aws:glue:eu-west-1:662195598891:database/*",
          "arn:aws:glue:eu-west-1:662195598891:table/*/*",
        ]
      },

      # S3 - bucket de staging Athena (résultats des queries)
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.athena_results.arn,
          "${aws_s3_bucket.athena_results.arn}/*"
        ]
      },

      # S3 - bucket de données (lecture seule sur les sources)
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
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

      # S3 - bucket de données (écriture sur les outputs dbt)
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.raw.arn,
          "${aws_s3_bucket.raw.arn}/*",
          aws_s3_bucket.staging.arn,
          "${aws_s3_bucket.staging.arn}/*",
          aws_s3_bucket.mart.arn,
          "${aws_s3_bucket.mart.arn}/*",
        ]
      }
    ]
  })
}

resource "aws_ecr_repository" "dagster_user_code" {
  name = "hymaia/discover-dagster"
  image_tag_mutability = "MUTABLE"
  force_delete = true
}

resource "aws_ecr_repository" "dagster_user_code_github_dbt" {
  name = "hymaia/github-dbt-project"
  image_tag_mutability = "MUTABLE"
  force_delete = true
}
