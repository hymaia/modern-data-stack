resource "aws_ecr_repository" "dagster_user_code" {
  name = "hymaia/discover-dagster"
  image_tag_mutability = "MUTABLE"
  force_delete = true
}
