terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Use fixed names for consistent deployment
# Note: GCS bucket exists and is managed externally

# Note: Artifact Registry repository created manually
# gcloud artifacts repositories create maf-policy-bot --repository-format=docker --location=us-central1

# Simple Cloud Run service deployment
resource "google_cloud_run_v2_service" "default" {
  name     = var.service_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    timeout = "300s"
    containers {
      image = "us-central1-docker.pkg.dev/${var.project_id}/maf-policy-bot/app:latest"
      
      startup_probe {
        initial_delay_seconds = 0
        timeout_seconds = 1
        period_seconds = 3
        failure_threshold = 1
        tcp_socket {
          port = 8080
        }
      }
      
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