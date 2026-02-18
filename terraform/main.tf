terraform {
  backend "gcs" {
    bucket  = "tfstate_data_project_2_jamagece"
    prefix  = "terraform/state" 
  }
}

resource "google_compute_network" "vpc_monitoreo_menores" {
  name = "vpc-monitoreo-menores"
  project = var.project_id
}

resource "google_compute_global_address" "rango_ip_monitoreo_menores" {
  name = "rango-ip-monitoreo-menores"
  purpose = "VPC_PEERING"
  address_type = "INTERNAL"
  network = google_compute_network.vpc_monitoreo_menores.id
  prefix_length = 16
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network = google_compute_network.vpc_monitoreo_menores.id
  service  = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.rango_ip_monitoreo_menores.name]
}

resource "google_storage_bucket" "bucket-menores" {
  name          = "bucket-fotos-menores-${var.project_id}"
  location      = var.region
  force_destroy = false
  storage_class = "STANDARD"
}

resource "google_storage_bucket" "dataflow-temp" {
  name          = "dataflow-temp-${var.project_id}"
  location      = var.region
  force_destroy = false
  storage_class = "STANDARD"
}

resource "google_pubsub_topic" "topic-ubicacion" {
  name = "topic-ubicacion"
}

resource "google_pubsub_subscription" "topic-ubicacion-sub" {
  name  = "${google_pubsub_topic.topic-ubicacion.name}-sub"
  topic = google_pubsub_topic.topic-ubicacion.name
}

resource "google_pubsub_topic" "topic-eventos" {
  name = "topic-eventos"
}

resource "google_pubsub_subscription" "topic-eventos-sub" {
  name  = "${google_pubsub_topic.topic-eventos.name}-sub"
  topic = google_pubsub_topic.topic-eventos.name
}


resource "google_pubsub_topic" "topic-user-notification" {
  name = "user-notification"
}

resource "google_sql_database_instance" "postgres_instance" {
  name                = "monitoreo-menores"
  region              = var.region
  database_version    = "POSTGRES_17"
  deletion_protection = false
  settings {
    edition           = "ENTERPRISE"
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_size         = 100

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc_monitoreo_menores.id
    }
  }
  lifecycle {
    prevent_destroy = true
  }
  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "random_password" "contraseña-monitoreo-menores" {
  length = 16
  special = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "google_sql_user" "postgres_user" {
  name     = "admin"
  instance = google_sql_database_instance.postgres_instance.name
  password = random_password.contraseña-monitoreo-menores.result
}

resource "google_sql_database" "menores_db" {
  name     = "menores_db"
  instance = google_sql_database_instance.postgres_instance.name
}

resource "google_bigquery_dataset" "monitoreo_dataset" {
  dataset_id = "monitoreo_dataset"
  project    = var.project_id
  location   = var.region
}

resource "google_bigquery_table" "menores" {
  dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
  table_id   = "menores"

  schema = <<EOF
[
  {"name": "id", "type": "STRING"},
  {"name": "nombre", "type": "STRING"},
  {"name": "apellidos", "type": "STRING"},
  {"name": "dni", "type": "STRING"},
  {"name": "fecha_nacimiento", "type": "STRING"},
  {"name": "direccion", "type": "STRING"},
  {"name": "url_foto", "type": "STRING"},
  {"name": "discapacidad", "type": "BOOLEAN"}

]
EOF
}

resource "google_bigquery_table" "adultos" {
  dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
  table_id   = "adultos"

  schema = <<EOF
[
  {"name": "id", "type": "STRING"},
  {"name": "nombre", "type": "STRING"},
  {"name": "apellidos", "type": "STRING"},
  {"name": "telefono", "type": "INT64"},
  {"name": "email", "type": "STRING"},
  {"name": "id_niño", "type": "STRING"}
]
EOF
}

resource "google_bigquery_table" "historico_ubicaciones" {
  dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
  table_id   = "historico_ubicacion"
  time_partitioning {
    type  = "DAY"
    field = "fecha"
  }
  schema = <<EOF
[
  {"name": "id", "type": "STRING"},
  {"name": "fecha", "type": "TIMESTAMP"},
  {"name": "latitud", "type": "FLOAT"},
  {"name": "longitud", "type": "FLOAT"},
  {"name": "radio", "type": "STRING"},
  {"name": "direccion", "type": "INT64"},
  {"name": "duracion", "type": "STRING"},
  {"name": "id_niño", "type": "STRING"}
]
EOF
}

resource "google_bigquery_table" "zona-restringida" {
  dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
  table_id   = "zona-restringida"

  schema = <<EOF
[
  {"name": "id", "type": "STRING"},
  {"name": "id_menor", "type": "STRING"},
  {"name": "nombre", "type": "STRING"},
  {"name": "latitud", "type": "FLOAT"},
  {"name": "longitud", "type": "FLOAT"},  
  {"name": "radio_advertencia", "type": "FLOAT"},
  {"name": "radio_peligro", "type": "FLOAT"}

]
EOF
}

resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

resource "google_firestore_document" "schema_ubicaciones" {
  project     = var.project_id
  database    = google_firestore_database.database.name
  collection  = "ubicaciones"
  document_id = "schema_info"

  fields = jsonencode({
    "descripcion" : { "stringValue" : "Ubicación en tiempo real. Un documento por niño." },
    "ejemplo" : { "stringValue" : "id_menor: Javi, lat: 39.4, long: -0.3, ultima_act: TIMESTAMP" }
  })
}

resource "google_firestore_document" "schema_notificaciones" {
  project     = var.project_id
  database    = google_firestore_database.database.name
  collection  = "notificaciones"
  document_id = "schema_info"

  fields = jsonencode({
    "descripcion" : { "stringValue" : "Log de alertas para Padres (Peligro) y Niños (Advertencia)" },
    "estructura" : { "stringValue" : "id_menor, tipo (PELIGRO/ADVERTENCIA), mensaje, fecha, destinatario" }
  })
}

resource "google_artifact_registry_repository" "repo_artifact" {
  location = var.region
  repository_id = "repo-data-project-2"
  format = "DOCKER"
}

resource "google_cloud_run_v2_service" "api_cloud_run" {
  name = "api-cloud-run"
  location = var.region
  deletion_protection = false
  template {
    service_account = google_service_account.api_cloud_run.email
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo_artifact.name}/api:latest"
      env {
        name = "PROYECTO_REGION_INSTANCIA"
        value = "${var.project_id}:${var.region}:${google_sql_database_instance.postgres_instance.name}"
      }
      env {
        name = "USUARIO_DB"
        value = google_sql_user.postgres_user.name
      }
      env {
        name = "CONTR_DB"
        value = google_sql_user.postgres_user.password
      }
      env {
        name = "NOMBRE_BD"
        value = google_sql_database.menores_db.name
      }
      env {
        name = "ID_PROYECTO"
        value = var.project_id
      }
      env {
        name = "TOPICO_UBICACIONES"
        value = google_pubsub_topic.topic-ubicacion.id
      }
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres_instance.connection_name]
      }
    }
  }
}
locals {
  api_hash = sha1(join("", [for f in fileset("${path.module}/../api", "**") : filesha1("${path.module}/../api/${f}")]))
}

resource "docker_image" "imagen_api" {
  name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo_artifact.name}/api:${local.api_hash}"
  build {
    context = "../api/"
    dockerfile = "Dockerfile"
  }
}

resource "docker_registry_image" "imagen_api_push" {
  name = docker_image.imagen_api.name
  keep_remotely = true
}

resource "local_file" "env_generadores" {
  filename = "${path.module}/../Generadores/.env"
  content  = <<-EOT
    BUCKET_FOTOS = ${google_storage_bucket.bucket-menores.name}
    URL_API = ${google_cloud_run_v2_service.api_cloud_run.uri}
  EOT
}
