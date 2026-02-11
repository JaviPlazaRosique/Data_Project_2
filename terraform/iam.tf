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
    role = each.key
    member = "serviceAccount:${google_service_account.api_cloud_run.email}"
}

resource "google_cloud_run_v2_service_iam_member" "uso_api_cloud_run" {
    location = google_cloud_run_v2_service.api_cloud_run.location
    name = google_cloud_run_v2_service.api_cloud_run.name
    role = "roles/run.invoker"
    member = "allUsers"
}
