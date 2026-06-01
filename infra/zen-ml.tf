resource "aws_rds_cluster" "zenml" {
  cluster_identifier  = "zenml"
  engine              = "aurora-mysql"
  engine_mode         = "provisioned"
  engine_version      = "8.0.mysql_aurora.3.08.0"
  database_name       = "zenml"
  master_username     = "zenml"
  master_password     = random_password.zenml_db.result

  db_subnet_group_name   = local.subnet_group_name
  vpc_security_group_ids = [aws_security_group.zenml_db.id]

  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 1

  serverlessv2_scaling_configuration {
    min_capacity             = 0.0
    max_capacity             = 2
    seconds_until_auto_pause = 360
  }

  tags = {
    Name = "zenml"
  }
}

resource "aws_rds_cluster_instance" "zenml" {
  identifier         = "zenml"
  cluster_identifier = aws_rds_cluster.zenml.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.zenml.engine
  engine_version     = aws_rds_cluster.zenml.engine_version

  db_subnet_group_name = local.subnet_group_name
}

resource "aws_security_group" "zenml_db" {
  name   = "zenml-db"
  vpc_id = local.vpc_id

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [module.kubernetes.cluster[0].cluster_primary_security_group_id]
  }
}

resource "random_password" "zenml_db" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "zenml_db" {
  name = "zen-ml/postgresql-auth"
}

resource "aws_secretsmanager_secret_version" "zenml_db" {
  secret_id = aws_secretsmanager_secret.zenml_db.id
  secret_string = jsonencode({
    username = "zenml"
    password = random_password.zenml_db.result
  })
}

resource "random_password" "zenml_encryption_key" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "zenml_encryption_key" {
  name = "zen-ml/encryption-key"
}

resource "aws_secretsmanager_secret_version" "zenml_encryption_key" {
  secret_id     = aws_secretsmanager_secret.zenml_encryption_key.id
  secret_string = random_password.zenml_encryption_key.result
}

resource "aws_iam_role" "zenml" {
  name               = "zenml"
  assume_role_policy = local.irsa_assume_policy["zenml"]
}

resource "aws_iam_role_policy" "zenml" {
  role = aws_iam_role.zenml.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
          "secretsmanager:ListSecrets",
          "secretsmanager:CreateSecret",
          "secretsmanager:UpdateSecret",
          "secretsmanager:PutSecretValue",
          "secretsmanager:DeleteSecret",
          "secretsmanager:TagResource",
        ]
        Resource = "arn:aws:secretsmanager:${local.region}:${data.aws_caller_identity.current.account_id}:secret:zenml/*"
      }
    ]
  })
}
