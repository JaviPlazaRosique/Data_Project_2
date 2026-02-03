variable "project_id" {
  description = "ID del proyecto en GCP"
  type = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "europe-southwest1"
}

variable "zone" {
  description = "The GCP zone"
  type        = string
  default     = "europe-southwest1-b"
}

variable "service_account_email" {
  description = "Email of the service account to attach to the VMs"
  type        = string
}
