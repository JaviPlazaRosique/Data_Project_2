variable "project_id" {
  description = "ID del proyecto en GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP"
  type = string
}

variable "servicios_gcp" {
  description = "URL de las APIs que deben de estar activas para el uso del proyecto"
  type = list(string)
  default = [
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "firestore.googleapis.com",
    "pubsub.googleapis.com",
    "compute.googleapis.com",
    "storage.googleapis.com",
    "bigquery.googleapis.com",
    "sqladmin.googleapis.com",
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "cloudfunctions.googleapis.com",
    "logging.googleapis.com", 
    "servicenetworking.googleapis.com"
  ]
}

#variables looker 
variable "looker_sa_id" {
  description = "ID único para la cuenta de servicio de Looker"
  type        = string
  default     = "looker-viz-sa"
}

variable "looker_dataset_id" {
  description = "Nombre del dataset de scratch para Looker"
  type        = string
  default     = "looker_scratch"
}

variable "looker_expiration_ms" {
  description = "Tiempo de vida de las tablas temporales en milisegundos (7 días por defecto)"
  type        = number
  default     = 604800000 
}