resource "aws_rds_cluster" "airbyte" {
  cluster_identifier  = "airbyte"
  engine              = "aurora-postgresql"
  engine_mode         = "provisioned"
  engine_version      = "16.4"
  database_name       = "airbyte"
  master_username     = "airbyte"
  master_password     = random_password.airbyte_db.result

  db_subnet_group_name   = local.subnet_group_name
  vpc_security_group_ids = [aws_security_group.airbyte_db.id]

  skip_final_snapshot = true
  deletion_protection = false
  backup_retention_period = 1

  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 2
  }

  tags = {
    Name = "airbyte"
  }
}

resource "aws_rds_cluster_instance" "airbyte" {
  identifier         = "airbyte"
  cluster_identifier = aws_rds_cluster.airbyte.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.airbyte.engine
  engine_version     = aws_rds_cluster.airbyte.engine_version

  db_subnet_group_name = local.subnet_group_name
}

resource "aws_security_group" "airbyte_db" {
  name   = "airbyte-db"
  vpc_id = local.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [module.kubernetes.cluster[0].cluster_primary_security_group_id]
  }
}

resource "random_password" "airbyte_db" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "airbyte_db" {
  name = "airbyte/postgresql"
}

resource "aws_secretsmanager_secret_version" "airbyte_db" {
  secret_id = aws_secretsmanager_secret.airbyte_db.id
  secret_string = jsonencode({
    user = "airbyte"
    password = random_password.airbyte_db.result
  })
}

resource "aws_iam_policy" "airbyte_s3" {
  name = "airbyte-s3"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:ListAllMyBuckets",
          "s3:GetObject*",
          "s3:PutObject",
          "s3:PutObjectAcl",
          "s3:DeleteObject",
          "s3:ListBucket*",
        ]
        Resource = [
          aws_s3_bucket.raw.arn,
          "${aws_s3_bucket.raw.arn}/*",
        ]
      },
      {
        Sid    = "GlueAccess"
        Effect = "Allow"
        Action = [
          "glue:TagResource",
          "glue:UnTagResource",
          "glue:BatchCreatePartition",
          "glue:BatchDeletePartition",
          "glue:BatchDeleteTable",
          "glue:BatchGetPartition",
          "glue:CreateDatabase",
          "glue:CreateTable",
          "glue:CreatePartition",
          "glue:DeletePartition",
          "glue:DeleteTable",
          "glue:GetDatabase",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:GetTable",
          "glue:GetTables",
          "glue:UpdateDatabase",
          "glue:UpdatePartition",
          "glue:UpdateTable",
        ]
        Resource = [
          "arn:aws:glue:eu-west-1:662195598891:catalog",
          "arn:aws:glue:eu-west-1:662195598891:database/*",
          "arn:aws:glue:eu-west-1:662195598891:table/*/*",
        ]
      }
    ]
  })
}

resource "aws_iam_role" "airbyte_s3" {
  name = "airbyte-s3"
  assume_role_policy = local.irsa_assume_policy["airbyte"]
}

resource "aws_iam_role_policy_attachment" "airbyte_s3" {
  role       = aws_iam_role.airbyte_s3.name
  policy_arn = aws_iam_policy.airbyte_s3.arn
}
