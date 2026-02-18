resource "google_service_account" "api_cloud_run" {
  account_id   = "api-cloud-run-sa"
  display_name = "Service Account para Cloud Run"
}

resource "google_project_iam_member" "api_cloud_run_roles" {
  for_each = toset([
    "roles/cloudsql.client",
    "roles/pubsub.publisher",
    "roles/storage.objectCreator",
    "roles/logging.logWriter",
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.api_cloud_run.email}"
}

# resource "google_cloud_run_v2_service_iam_member" "uso_api_cloud_run" {
#   location = google_cloud_run_v2_service.api_cloud_run.location
#   name     = google_cloud_run_v2_service.api_cloud_run.name
#   role     = "roles/run.invoker"
#   member   = "allUsers"
# }


# SERVICE ACCOUNT DE DATAFLOW 
resource "google_service_account" "dataflow_sa" {
  account_id   = "dataflow-worker-sa"
  display_name = "Service Account para Dataflow Pipeline"
}

resource "google_project_iam_member" "dataflow_permissions" {
  for_each = toset([
    "roles/dataflow.admin",      # Administrar el trabajo
    "roles/dataflow.worker",     # Permiso base para que las máquinas procesen
    "roles/pubsub.subscriber",   # Leer los mensajes de ubicaciones
    "roles/bigquery.dataEditor", # Escribir en la tabla de histórico
    "roles/bigquery.jobUser",    # Permiso para ejecutar trabajos de BigQuery
    "roles/datastore.user",      # Escribir en Firestore
    "roles/storage.objectAdmin", # Escribir archivos temporales en el Bucket
    "roles/pubsub.publisher",    # Publicar mensajes de error en Pub/Sub
    "roles/viewer"               # Permisos de solo lectura para acceder a recursos necesarios
  ])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.dataflow_sa.email}"
}

resource "google_cloud_run_v2_service_iam_member" "public_access_ws" {
  location = google_cloud_run_v2_service.ws_server.location
  name     = google_cloud_run_v2_service.ws_server.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}