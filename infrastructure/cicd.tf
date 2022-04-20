module "pipeline" {
  # source                = "git@github.com:mentorpal/terraform-modules//modules/trunk_cicd_pipeline?ref=tags/v3.2.3"
  source                  = "git@github.com:mentorpal/terraform-modules//modules/trunk_cicd_pipeline?ref=cicd"
  codestar_connection_arn = var.codestar_connection_arn
  project_name            = "mentor-classifier-service"
  github_repo_name        = "classifier-service"
  build_cache_type        = "NO_CACHE"
  deploy_cache_type       = "NO_CACHE"
  build_compute_type      = "BUILD_GENERAL1_SMALL"
  deploys_compute_type    = "BUILD_GENERAL1_SMALL"

  build_buildspec          = "cicd/buildspec.yml"
  deploy_staging_buildspec = "cicd/deployspec_staging.yml"
  deploy_prod_buildspec    = "cicd/deployspec_prod.yml"

  allow_git_folder_access_in_pipeline_build = true
  export_pipeline_info                      = true

  tags = {
    Source  = "terraform"
  }

  providers = {
    aws = aws.us_east_1
  }
}
