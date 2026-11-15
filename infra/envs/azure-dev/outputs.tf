# These outputs are the DF_DBX_* settings of the worker (docs/databricks.md).

output "df_dbx_host" {
  value = module.workspace.workspace_url
}

output "df_dbx_http_path" {
  value = module.warehouse.http_path
}

output "df_dbx_catalog" {
  value = module.catalog.catalog_name
}

output "df_dbx_platform_client_id" {
  value = module.principals.platform_application_id
}

output "df_dbx_platform_client_secret" {
  value     = module.principals.platform_client_secret
  sensitive = true
}

output "df_dbx_learner_client_ids" {
  description = "One for each worker."
  value       = module.principals.learner_application_ids
}

output "df_dbx_learner_client_secrets" {
  description = "One for each worker, in the same order as the client ids."
  value       = module.principals.learner_client_secrets
  sensitive   = true
}
