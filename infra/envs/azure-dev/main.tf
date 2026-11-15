# DataForge lab platform on Azure: development environment.
# `terraform apply` creates all of it. `terraform destroy` removes all of it.

locals {
  name = "dataforge-${var.environment}"
  tags = {
    project     = "dataforge"
    environment = var.environment
    managed_by  = "terraform"
  }
}

resource "random_string" "storage" {
  length  = 6
  upper   = false
  special = false
}

module "workspace" {
  source = "../../modules/databricks-workspace"

  resource_group_name = "rg-${local.name}"
  workspace_name      = "dbw-${local.name}"
  location            = var.location
  tags                = local.tags
}

module "principals" {
  source = "../../modules/service-principals"

  name_prefix   = local.name
  learner_count = var.learner_count
}

module "catalog" {
  source = "../../modules/unity-catalog"

  catalog_name         = var.catalog_name
  resource_group_name  = module.workspace.resource_group_name
  location             = module.workspace.location
  storage_account_name = "stdataforge${var.environment}${random_string.storage.result}"
  platform_principal   = module.principals.platform_application_id
  learner_principals   = module.principals.learner_application_ids
  tags                 = local.tags
}

module "warehouse" {
  source = "../../modules/sql-warehouse"

  name           = "${local.name}-lab"
  auto_stop_mins = var.warehouse_auto_stop_mins
  principals = concat(
    [module.principals.platform_application_id],
    module.principals.learner_application_ids,
  )
}
