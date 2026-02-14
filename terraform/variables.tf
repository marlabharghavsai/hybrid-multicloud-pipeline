############################################################
# GCP PROJECT ID
############################################################
variable "gcp_project_id" {
  description = "GCP Project ID"
  type        = string
}

############################################################
# GCP REGION
############################################################
variable "gcp_region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

############################################################
# GCP KEYFILE PATH
############################################################
variable "gcp_keyfile_path" {
  description = "Path to GCP service account key file"
  type        = string
}

