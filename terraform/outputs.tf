output "service_url" {
  description = "Expected URL of the Cloud Run service"
  value       = local.service_url
}

output "build_trigger_id" {
  description = "Cloud Build trigger ID"
  value       = google_cloudbuild_trigger.deploy_trigger.id
}