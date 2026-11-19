# One small serverless SQL warehouse that all lesson runs share.

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
  }
}

resource "databricks_sql_endpoint" "lab" {
  name                      = var.name
  cluster_size              = var.cluster_size
  min_num_clusters          = 1
  max_num_clusters          = var.max_num_clusters
  auto_stop_mins            = var.auto_stop_mins
  enable_serverless_compute = true
  warehouse_type            = "PRO"

  tags {
    custom_tags {
      key   = "project"
      value = "dataforge"
    }
  }
}

# The principals can run queries on the warehouse. They cannot change it.
resource "databricks_permissions" "lab" {
  sql_endpoint_id = databricks_sql_endpoint.lab.id

  dynamic "access_control" {
    for_each = toset(var.principals)
    content {
      service_principal_name = access_control.value
      permission_level       = "CAN_USE"
    }
  }
}
