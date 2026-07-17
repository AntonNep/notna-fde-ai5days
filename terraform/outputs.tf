output "telemetry_bucket" {
  value       = google_storage_bucket.logs_bucket.name
  description = "The name of the GCS bucket created for telemetry traces."
}

output "artifact_registry_uri" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.image_repo.repository_id}"
  description = "The base URI for pushing container images."
}

output "service_account_email" {
  value       = google_service_account.agent_runner_sa.email
  description = "The service account email dedicated to agent execution."
}
