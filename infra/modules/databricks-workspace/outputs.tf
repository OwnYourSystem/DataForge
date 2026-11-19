output "workspace_id" {
  description = "Azure resource id of the workspace."
  value       = azurerm_databricks_workspace.this.id
}

output "workspace_url" {
  description = "Host name of the workspace, without https://."
  value       = azurerm_databricks_workspace.this.workspace_url
}

output "resource_group_name" {
  value = azurerm_resource_group.this.name
}

output "location" {
  value = azurerm_resource_group.this.location
}
