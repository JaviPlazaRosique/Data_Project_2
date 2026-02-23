variable "project_id" {
  description = "ID del proyecto en GCP"
  type        = string
}

variable "region" {
  description = "Region de GCP"
  type = string
}

variable "region_df" {
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
    "servicenetworking.googleapis.com",
    "datastream.googleapis.com",
    "dataflow.googleapis.com"
  ]
}
