# Creates the storage for Terraform state. Run this one time, with local
# state, before the first `terraform init` of an environment.
# This is the one part that cannot keep its own state in remote storage.

terraform {
  required_version = ">= 1.9.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
  # The storage account has no access keys. Use the Entra identity.
  storage_use_azuread = true
}

variable "subscription_id" {
  description = "Azure subscription that holds the state storage."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "northeurope"
}

resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
}

resource "azurerm_resource_group" "state" {
  name     = "rg-dataforge-tfstate"
  location = var.location
  tags     = { project = "dataforge", managed_by = "terraform" }
}

resource "azurerm_storage_account" "state" {
  name                            = "stdataforgetf${random_string.suffix.result}"
  resource_group_name             = azurerm_resource_group.state.name
  location                        = azurerm_resource_group.state.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  # State holds secrets. Only Microsoft Entra identities can read it.
  shared_access_key_enabled = false

  blob_properties {
    versioning_enabled = true
    delete_retention_policy {
      days = 30
    }
  }

  tags = { project = "dataforge", managed_by = "terraform" }
}

resource "azurerm_storage_container" "state" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.state.id
  container_access_type = "private"
}

output "backend_config" {
  description = "Put these values in infra/envs/<env>/backend.hcl."
  value = {
    resource_group_name  = azurerm_resource_group.state.name
    storage_account_name = azurerm_storage_account.state.name
    container_name       = azurerm_storage_container.state.name
  }
}
