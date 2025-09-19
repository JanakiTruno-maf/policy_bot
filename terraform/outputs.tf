output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.default.uri
}

output "terraform_state_bucket" {
  description = "Terraform state bucket name"
  value       = "${var.project_id}-maf-policy-bot-terraform-state"
}