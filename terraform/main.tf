terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Random suffix for unique bucket name
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# GCS bucket for Terraform state
resource "google_storage_bucket" "terraform_state" {
  name          = "${var.project_id}-tf-state-${random_id.bucket_suffix.hex}"
  location      = var.region
  force_destroy = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      num_newer_versions = 3
    }
    action {
      type = "Delete"
    }
  }
}

# Note: Artifact Registry repository created manually
# gcloud artifacts repositories create maf-policy-bot --repository-format=docker --location=us-central1

# Simple Cloud Run service deployment
resource "google_cloud_run_v2_service" "default" {
  name     = "${var.service_name}-${random_id.bucket_suffix.hex}"
  location = var.region

  template {
    containers {
      image = "us-central1-docker.pkg.dev/${var.project_id}/maf-policy-bot/app:latest"
      
      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "VERTEX_LOCATION"
        value = var.region
      }

      env {
        name  = "RAG_CORPUS_RESOURCE"
        value = "projects/${var.project_id}/locations/us-east4/ragCorpora/4035225266123964416"
      }

      env {
        name  = "VERTEX_MODEL_NAME"
        value = "gemini-2.0-flash-001"
      }

      env {
        name  = "SECRET_KEY"
        value = "tobacco-legal-info-system-2024"
      }

      env {
        name  = "GOOGLE_CLIENT_ID"
        value = var.google_client_id
      }

      env {
        name  = "GOOGLE_CLIENT_SECRET"
        value = var.google_client_secret
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }
}

# Note: Allow unauthenticated access will be set via Cloud Build deployment

data "google_client_config" "default" {}