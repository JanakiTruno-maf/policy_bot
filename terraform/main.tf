terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "maf-policy-bot-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# GCS bucket for Terraform state
resource "google_storage_bucket" "terraform_state" {
  name          = "maf-policy-bot-terraform-state"
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

# Artifact Registry repository
resource "google_artifact_registry_repository" "repo" {
  location      = var.region
  repository_id = var.service_name
  description   = "Docker repository for ${var.service_name}"
  format        = "DOCKER"
}

# Build and push Docker image
resource "null_resource" "docker_build" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ..
      docker build -t ${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}/${var.service_name}:latest .
      docker push ${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}/${var.service_name}:latest
    EOT
  }

  depends_on = [google_artifact_registry_repository.repo]
}

# Cloud Run service
resource "google_cloud_run_v2_service" "default" {
  name     = var.service_name
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.service_name}/${var.service_name}:latest"
      
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
        value = var.rag_corpus_resource
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

  depends_on = [null_resource.docker_build]
}

# Allow unauthenticated access
resource "google_cloud_run_v2_service_iam_binding" "default" {
  location = google_cloud_run_v2_service.default.location
  name     = google_cloud_run_v2_service.default.name
  role     = "roles/run.invoker"
  members = [
    "allUsers"
  ]
}