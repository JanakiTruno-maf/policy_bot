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

# Use Cloud Build to build and deploy
resource "google_cloudbuild_trigger" "deploy_trigger" {
  name        = "${var.service_name}-deploy"
  description = "Deploy ${var.service_name} to Cloud Run"

  github {
    owner = "JanakiTruno-maf"
    name  = "policy_bot"
    push {
      branch = "main"
    }
  }

  build {
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "build",
        "-t",
        "gcr.io/${var.project_id}/${var.service_name}:latest",
        "."
      ]
    }
    
    step {
      name = "gcr.io/cloud-builders/docker"
      args = [
        "push",
        "gcr.io/${var.project_id}/${var.service_name}:latest"
      ]
    }
    
    step {
      name = "gcr.io/cloud-builders/gcloud"
      args = [
        "run",
        "deploy",
        var.service_name,
        "--image=gcr.io/${var.project_id}/${var.service_name}:latest",
        "--region=${var.region}",
        "--allow-unauthenticated",
        "--set-env-vars=GOOGLE_CLOUD_PROJECT=${var.project_id},VERTEX_LOCATION=${var.region},RAG_CORPUS_RESOURCE=${var.rag_corpus_resource}"
      ]
    }
  }
}

# Cloud Run service will be created by Cloud Build
# Just output the expected service URL
locals {
  service_url = "https://${var.service_name}-${random_id.bucket_suffix.hex}-${data.google_client_config.default.region}-${data.google_client_config.default.project}.a.run.app"
}

data "google_client_config" "default" {}