# The lab catalog, with its own storage, and the catalog-level grants.
#
# The catalog has its own managed storage so that `terraform destroy` removes
# all lab data, and so that the catalog does not depend on storage at the
# metastore level.

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.50"
    }
  }
}

resource "azurerm_storage_account" "catalog" {
  name                            = var.storage_account_name
  resource_group_name             = var.resource_group_name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  is_hns_enabled                  = true
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = var.tags
}

resource "azurerm_storage_container" "catalog" {
  name                  = "catalog"
  storage_account_id    = azurerm_storage_account.catalog.id
  container_access_type = "private"
}

# The identity that Unity Catalog uses to read and write the storage.
resource "azurerm_databricks_access_connector" "catalog" {
  name                = "${var.catalog_name}-access"
  resource_group_name = var.resource_group_name
  location            = var.location
  tags                = var.tags

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_role_assignment" "catalog_storage" {
  scope                = azurerm_storage_account.catalog.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.catalog.identity[0].principal_id
}

resource "databricks_storage_credential" "catalog" {
  name    = "${var.catalog_name}_credential"
  comment = "Managed by Terraform. Storage for the catalog ${var.catalog_name}."

  azure_managed_identity {
    access_connector_id = azurerm_databricks_access_connector.catalog.id
  }

  depends_on = [azurerm_role_assignment.catalog_storage]
}

resource "databricks_external_location" "catalog" {
  name            = "${var.catalog_name}_location"
  url             = "abfss://${azurerm_storage_container.catalog.name}@${azurerm_storage_account.catalog.name}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.catalog.name
  comment         = "Managed by Terraform. Storage for the catalog ${var.catalog_name}."
  # Lab data only: let `terraform destroy` remove the location with its data.
  force_destroy = true
}

resource "databricks_catalog" "lab" {
  name         = var.catalog_name
  comment      = "DataForge lab catalog. One schema for each lesson run. Managed by Terraform."
  storage_root = databricks_external_location.catalog.url
  # Run schemas are made by the platform principal, not by Terraform.
  force_destroy = true
}

# Catalog-level grants. `databricks_grants` is authoritative: a grant that is
# not in this block is removed at the next apply.
resource "databricks_grants" "lab" {
  catalog = databricks_catalog.lab.name

  # Trusted. Makes and drops run schemas, loads lesson data, reads results.
  grant {
    principal  = var.platform_principal
    privileges = ["USE_CATALOG", "USE_SCHEMA", "CREATE_SCHEMA", "SELECT"]
  }

  # Not trusted. Can enter the catalog and nothing more. The platform
  # principal gives it rights on one run schema at the start of each run.
  dynamic "grant" {
    for_each = toset(var.learner_principals)
    content {
      principal  = grant.value
      privileges = ["USE_CATALOG"]
    }
  }
}
