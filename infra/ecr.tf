resource "aws_ecr_repository" "dagster_user_code" {
  name = "hymaia/discover-dagster"
  image_tag_mutability = "MUTABLE"
  force_delete = true
}

resource "aws_ecr_repository" "dagster_user_code_github_dbt" {
  name = "hymaia/github-dbt-project"
  image_tag_mutability = "MUTABLE"
  force_delete = true
}
