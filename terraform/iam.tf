resource "google_service_account" "api_cloud_run" {
  account_id = "api-cloud-run-sa"
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
  role = each.key
  member = "serviceAccount:${google_service_account.api_cloud_run.email}"
}

resource "google_cloud_run_v2_service_iam_member" "uso_api_cloud_run" {
  location = google_cloud_run_v2_service.api_cloud_run.location
  name = google_cloud_run_v2_service.api_cloud_run.name
  role = "roles/run.invoker"
  member = "allUsers"
}


resource "google_service_account" "dataflow_sa" {
  account_id = "dataflow-worker-sa"
  display_name = "Service Account para Dataflow Pipeline"
}

resource "google_project_iam_member" "dataflow_permissions" {
  for_each = toset([
    "roles/dataflow.admin",      
    "roles/dataflow.worker",     
    "roles/pubsub.subscriber",   
    "roles/bigquery.dataEditor", 
    "roles/bigquery.jobUser",    
    "roles/datastore.user",      
    "roles/storage.objectAdmin", 
    "roles/pubsub.publisher",    
    "roles/viewer",         
    "roles/cloudsql.client"      
  ])

  project = var.project_id
  role = each.key
  member = "serviceAccount:${google_service_account.dataflow_sa.email}"
}

resource "google_service_account" "web_cloud_run" {
    account_id = "web-cloud-run-sa"
    display_name = "Service Account para Cloud Run WEB"
}

resource "google_project_iam_member" "web_cloud_run_roles" {
    for_each = toset([
        "roles/cloudsql.client",
        "roles/datastore.user",
        "roles/storage.objectUser",
        "roles/logging.logWriter",
        "roles/storage.objectViewer"
        ])
    project = var.project_id
    role = each.key
    member = "serviceAccount:${google_service_account.web_cloud_run.email}"
}

resource "google_cloud_run_v2_service_iam_member" "uso_web_cloud_run" {
    location = google_cloud_run_v2_service.web_cloud_run.location
    name = google_cloud_run_v2_service.web_cloud_run.name
    role = "roles/run.invoker"
    member = "allUsers"
}

resource "google_project_service_identity" "datastream_sa" {
  provider = google-beta
  project = var.project_id
  service = "datastream.googleapis.com"
}

resource "google_bigquery_dataset_iam_member" "datastream_bq_editor" {
  project = var.project_id
  dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
  role = "roles/bigquery.dataEditor" 
  member = "serviceAccount:${google_project_service_identity.datastream_sa.email}"
}