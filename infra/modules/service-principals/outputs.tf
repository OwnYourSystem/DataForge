output "platform_application_id" {
  description = "Client id of the platform principal. Also its name in grants."
  value       = databricks_service_principal.platform.application_id
}

output "platform_client_secret" {
  value     = databricks_service_principal_secret.platform.secret
  sensitive = true
}

output "learner_application_ids" {
  description = "Client ids of the learner principals. Also their names in grants."
  value       = databricks_service_principal.learner[*].application_id
}

output "learner_client_secrets" {
  value     = databricks_service_principal_secret.learner[*].secret
  sensitive = true
}
