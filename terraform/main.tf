terraform {
  required_version = ">= 1.3.0"
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

# Enable required GCP APIs
resource "google_project_service" "enabled_services" {
  for_each = toset([
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
    "storage.googleapis.com"
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# Create a Cloud Storage Bucket for logging and telemetry traces
resource "google_storage_bucket" "logs_bucket" {
  name                        = "${var.project_id}-${var.app_name}-telemetry-logs"
  location                    = var.region
  force_destroy               = true
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    condition {
      age = 30
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.enabled_services]
}

# Create an Artifact Registry Repository for the container image
resource "google_artifact_registry_repository" "image_repo" {
  location      = var.region
  repository_id = "${var.app_name}-repo"
  description   = "Docker repository for EmberScale dragon agent image"
  format        = "DOCKER"

  depends_on = [google_project_service.enabled_services]
}

# Create a Dedicated Service Account for agent execution (Runtime Identity)
resource "google_service_account" "agent_runner_sa" {
  account_id   = "${var.app_name}-runner-sa"
  display_name = "EmberScale Agent Runtime Service Account"
  project      = var.project_id
}

# Grant Vertex AI User role to the service account
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.agent_runner_sa.email}"
}

# Grant GCS storage object creator and viewer role to the service account
resource "google_project_iam_member" "storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.agent_runner_sa.email}"
}

# Grant Secrets Accessor role to read sensitive keys securely
resource "google_project_iam_member" "secrets_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.agent_runner_sa.email}"
}
