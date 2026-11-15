output "id" {
  value = databricks_sql_endpoint.lab.id
}

output "http_path" {
  description = "HTTP path for dbt and for the SQL connector."
  value       = databricks_sql_endpoint.lab.odbc_params[0].path
}
