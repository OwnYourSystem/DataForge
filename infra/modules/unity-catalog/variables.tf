variable "catalog_name" {
  description = "Name of the lab catalog. Lowercase letters, digits and underscores."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9_]{0,62}$", var.catalog_name))
    error_message = "Use lowercase letters, digits and underscores. Start with a letter."
  }
}

variable "resource_group_name" {
  description = "Resource group for the catalog storage."
  type        = string
}

variable "location" {
  description = "Azure region of the workspace."
  type        = string
}

variable "storage_account_name" {
  description = "Globally unique name of the storage account for the catalog."
  type        = string
}

variable "platform_principal" {
  description = "Application id of the platform service principal."
  type        = string
}

variable "learner_principals" {
  description = "Application ids of the learner service principals."
  type        = list(string)
}

variable "tags" {
  description = "Tags for Azure resources."
  type        = map(string)
  default     = {}
}
