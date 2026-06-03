resource "aws_rds_cluster" "mlflow" {
  cluster_identifier = "mlflow"
  engine             = "aurora-postgresql"
  engine_mode        = "provisioned"
  engine_version     = "16.11"
  database_name      = "mlflow"
  master_username    = "mlflow"
  master_password    = random_password.mlflow_db.result

  db_subnet_group_name   = local.subnet_group_name
  vpc_security_group_ids = [aws_security_group.mlflow_db.id]

  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 1

  serverlessv2_scaling_configuration {
    min_capacity             = 0.0
    max_capacity             = 2
    seconds_until_auto_pause = 360
  }

  tags = {
    Name = "mlflow"
  }
}

resource "aws_rds_cluster_instance" "mlflow" {
  identifier         = "mlflow"
  cluster_identifier = aws_rds_cluster.mlflow.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.mlflow.engine
  engine_version     = aws_rds_cluster.mlflow.engine_version

  db_subnet_group_name = local.subnet_group_name
}

resource "aws_security_group" "mlflow_db" {
  name   = "mlflow-db"
  vpc_id = local.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.kubernetes.cluster[0].cluster_primary_security_group_id]
  }
}

resource "random_password" "mlflow_db" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "mlflow_db" {
  name = "mlflow/postgresql-auth"
}

resource "aws_secretsmanager_secret_version" "mlflow_db" {
  secret_id = aws_secretsmanager_secret.mlflow_db.id
  secret_string = jsonencode({
    username = "mlflow"
    password = random_password.mlflow_db.result
  })
}

resource "random_password" "mlflow_admin" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "mlflow_admin" {
  name = "mlflow/admin-auth"
}

resource "aws_secretsmanager_secret_version" "mlflow_admin" {
  secret_id = aws_secretsmanager_secret.mlflow_admin.id
  secret_string = jsonencode({
    username = "admin"
    password = random_password.mlflow_admin.result
  })
}

resource "aws_s3_bucket" "mlflow_artifacts" {
  bucket = "mlflow-artifacts-${local.account_id}"

  tags = {
    Name = "mlflow-artifacts"
  }
}

resource "aws_s3_bucket_versioning" "mlflow_artifacts" {
  bucket = aws_s3_bucket.mlflow_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_iam_role" "mlflow" {
  name               = "mlflow"
  assume_role_policy = local.irsa_assume_policy["mlflow"]
}

resource "aws_iam_role_policy" "mlflow" {
  role = aws_iam_role.mlflow.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject",
          "s3:DeleteObject",
        ]
        Resource = [
          aws_s3_bucket.mlflow_artifacts.arn,
          "${aws_s3_bucket.mlflow_artifacts.arn}/*",
        ]
      },
    ]
  })
}
