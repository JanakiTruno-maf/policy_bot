# This file will be used after initial deployment to migrate state to GCS
# Run: terraform init -migrate-state after first apply

# terraform {
#   backend "gcs" {
#     bucket = "bat-bigquery-maf-policy-bot-terraform-state"
#     prefix = "terraform/state"
#   }
# }