module "tracking_data_access" {
  source                                     = "git@github.com:hymaia/data-platform-terraform-module.git//modules/tracking-data-access-aws/infra"
  athena_tracking_data_access_workgroup_name = "audit-data-access"
  bucket_tracking_data_name                  = "audit-data-access"
  database_tracking_data_name                = "audit"
  table_tracking_data_name                   = "read_actions"
}
