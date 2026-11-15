variable "resource_group_name" {
  description = "Resource group for the workspace and its storage."
  type        = string
}

variable "workspace_name" {
  description = "Name of the Databricks workspace."
  type        = string
}

variable "location" {
  description = "Azure region. It must support serverless SQL warehouses."
  type        = string
}

variable "tags" {
  description = "Tags for all resources."
  type        = map(string)
  default     = {}
}
