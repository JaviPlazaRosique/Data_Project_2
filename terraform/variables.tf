variable "project_id" {
  description = "ID del proyecto en GCP"
  type = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "zone" {
  description = "The GCP zone"
  type        = string
}

variable "service_account_email" {
  description = "Email of the service account to attach to the VMs"
  type        = string
}

variable "password-postgres" {
  description = "The password for the postgres user in Cloud SQL"
  type        = string
}