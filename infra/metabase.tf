resource "aws_rds_cluster" "metabase" {
  cluster_identifier  = "metabase"
  engine              = "aurora-postgresql"
  engine_mode         = "provisioned"
  engine_version      = "16.4"
  database_name       = "metabase"
  master_username     = "metabase"
  master_password     = random_password.metabase_db.result

  db_subnet_group_name   = local.subnet_group_name
  vpc_security_group_ids = [aws_security_group.metabase_db.id]

  skip_final_snapshot = true
  deletion_protection = false
  backup_retention_period = 1

  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 2
  }

  tags = {
    Name = "metabase"
  }
}

resource "aws_rds_cluster_instance" "metabase" {
  identifier         = "metabase"
  cluster_identifier = aws_rds_cluster.metabase.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.metabase.engine
  engine_version     = aws_rds_cluster.metabase.engine_version

  db_subnet_group_name = local.subnet_group_name
}

resource "aws_security_group" "metabase_db" {
  name   = "metabase-db"
  vpc_id = local.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.kubernetes.cluster[0].cluster_primary_security_group_id]
  }
}

resource "random_password" "metabase_db" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "metabase_db" {
  name = "metabase/postgresql"
}

resource "aws_secretsmanager_secret_version" "metabase_db" {
  secret_id = aws_secretsmanager_secret.metabase_db.id
  secret_string = jsonencode({
    username = "metabase"
    password = random_password.metabase_db.result
  })
}

resource "aws_iam_role" "metabase" {
  name = "metabase"
  assume_role_policy = local.irsa_assume_policy["metabase"]
}

resource "aws_iam_role_policy" "metabase" {
  role = aws_iam_role.metabase.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "athena:*",
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions",
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Resource = [
          aws_s3_bucket.mart.arn,
          "${aws_s3_bucket.mart.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = [
          aws_s3_bucket.athena_results.arn,
          "${aws_s3_bucket.athena_results.arn}/*"
        ]
      }
    ]
  })
}
