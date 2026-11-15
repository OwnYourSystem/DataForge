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
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Remote state with locking (blob lease). The storage comes from
  # infra/bootstrap/azure-state. Give its names in backend.hcl:
  #   terraform init -backend-config=backend.hcl
  backend "azurerm" {
    key              = "azure-dev.tfstate"
    use_azuread_auth = true
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# The Databricks provider signs in to the new workspace with the same Azure
# identity that runs Terraform. That identity is the first workspace admin.
provider "databricks" {
  host                        = "https://${module.workspace.workspace_url}"
  azure_workspace_resource_id = module.workspace.workspace_id
}
