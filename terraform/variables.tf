variable "project_id" {
  type        = string
  description = "The Google Cloud Project ID where resources will be provisioned."
}

variable "region" {
  type        = string
  default     = "us-east1"
  description = "The target region for GCP resources."
}

variable "app_name" {
  type        = string
  default     = "emberscale"
  description = "The application name used for resource naming."
}
