# The 2 kinds of identity of the lab (see docs/adr/004-run-isolation.md):
# one trusted platform principal, and one learner principal for each worker.

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
  }
}

resource "databricks_service_principal" "platform" {
  display_name               = "${var.name_prefix}-platform"
  databricks_sql_access      = true
  workspace_access           = false
  allow_cluster_create       = false
  allow_instance_pool_create = false
}

resource "databricks_service_principal" "learner" {
  count                      = var.learner_count
  display_name               = "${var.name_prefix}-learner-${count.index + 1}"
  databricks_sql_access      = true
  workspace_access           = false
  allow_cluster_create       = false
  allow_instance_pool_create = false
}

# OAuth secrets. The values are in the Terraform state, so the state storage
# must be private (see infra/bootstrap/azure-state).
resource "databricks_service_principal_secret" "platform" {
  service_principal_id = databricks_service_principal.platform.id
}

resource "databricks_service_principal_secret" "learner" {
  count                = var.learner_count
  service_principal_id = databricks_service_principal.learner[count.index].id
}
