# infra/dagster-rds.tf

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
    min_capacity = 0.5
    max_capacity = 2
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
