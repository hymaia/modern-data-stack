resource "aws_autoscaling_schedule" "scale_down_evening" {
  scheduled_action_name  = "${local.prefix}-scale-down-evening"
  min_size               = 0
  max_size               = 5
  desired_capacity       = 0
  recurrence             = "0 0 * * *"
  time_zone              = "Europe/Paris"
  autoscaling_group_name = module.kubernetes.cluster[0].eks_managed_node_groups_autoscaling_group_names[0]
}
#
# resource "aws_autoscaling_schedule" "scale_up_morning" {
#   scheduled_action_name  = "${local.prefix}-scale-up-morning"
#   min_size               = 0
#   max_size               = 5
#   desired_capacity       = 3
#   recurrence             = "0 12 * * *"
#   time_zone              = "Europe/Paris"
#   autoscaling_group_name = module.kubernetes.cluster[0].eks_managed_node_groups_autoscaling_group_names[0]
# }

resource "aws_autoscaling_schedule" "spark_scale_down_evening" {
  scheduled_action_name  = "${local.prefix}-spark-scale-down-evening"
  min_size               = 0
  max_size               = 5
  desired_capacity       = 0
  recurrence             = "0 0 * * *"
  time_zone              = "Europe/Paris"
  autoscaling_group_name = module.kubernetes.cluster[0].eks_managed_node_groups_autoscaling_group_names[1]
}

