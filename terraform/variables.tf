variable "project_id" {
  description = "ID del proyecto en GCP"
  type = string
}

variable "region" {
  description = "Region de GCP"
  type        = string
}

variable "zone" {
  description = "Zona de GCP"
  type        = string
}

variable "service_account_email" {
  description = "Email de service account para guardar VMs"
  type        = string
}

variable "password-postgres" {
  description = "Tla contraseña para el usuario de postgres en Cloud SQL"
  type        = string
}