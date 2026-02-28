data "aws_caller_identity" "current" {}

data "aws_acm_certificate" "fcussac_app" {
  domain = local.dns_zone
}

locals {
  account_id = data.aws_caller_identity.current.account_id
  prefix = "hyma-mds"
  region = "eu-west-1"
  dns_zone = "fcussac.app.hymaia.com"
}
