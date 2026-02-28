data "aws_caller_identity" "current" {}

data "aws_acm_certificate" "fcussac_app" {
  domain = local.dns_zone
}

locals {
  account_id = data.aws_caller_identity.current.account_id
  prefix = "hyma-mds"
  region = "eu-west-1"
  dns_zone = "fcussac.app.hymaia.com"
  vpc_id = module.kubernetes.cluster_network.internal.network[0].vpc_id
  subnet_group_name = module.kubernetes.cluster_network.internal.network[0].database_subnet_group_name
}
