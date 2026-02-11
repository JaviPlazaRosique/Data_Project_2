# terraform {
#   backend "gcs" {
#     bucket  = "tfstate_data_project_2_jamagece"
#     prefix  = "terraform/state" 
#   }
# }

# GCS Buckets
resource "google_storage_bucket" "bucket-menores" {
         name = "bucket-fotos-menores"
         location = var.region
         force_destroy = true
         storage_class = "STANDARD"
}
resource "google_storage_bucket" "dataflow-temp" {
  name          = "dataflow-jamagece" 
  location      = var.region
  force_destroy = true
  storage_class = "STANDARD"
}

# Pub/Sub topic and subscription
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

# Postgres SQL instance
resource "google_sql_database_instance" "postgres_instance" {
  name             = "monitoreo-menores"
  region           = var.region
  database_version = "POSTGRES_15"
  deletion_protection = false
  settings {
    tier            = "db-f1-micro"
    availability_type = "ZONAL"
    disk_size       = 100 # GB
    

    ip_configuration {
      ipv4_enabled = true
    }
  }
  lifecycle {
    prevent_destroy = false
  }
}
resource "google_sql_user" "postgres_user" {
  name     = "postgres"
  instance = google_sql_database_instance.postgres_instance.name
  password = var.password-postgres
}

resource "google_sql_database" "menores_db" {
  name     = "menores_db"
  instance = google_sql_database_instance.postgres_instance.name
}

# BigQuery Resources
resource "google_bigquery_dataset" "monitoreo_dataset" {
  dataset_id  = "monitoreo_dataset"
  project     = var.project_id
  location    = var.region
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
  {"name": "telefono", "type": "STRING"},
  {"name": "id_menor", "type": "STRING"},
  {"name": "email", "type": "STRING"}

]
EOF
}

resource "google_bigquery_table" "historico_ubicaciones" {
  dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
  table_id   = "historico_ubicaciones"
  time_partitioning {
      type  = "DAY"
      field = "fecha"
    }
  schema = <<EOF
[
  {"name": "id", "type": "STRING"},  
  {"name": "id_menor", "type": "STRING"},
  {"name": "latitud", "type": "FLOAT"},
  {"name": "longitud", "type": "FLOAT"},
  {"name": "radio", "type": "FLOAT"},
  {"name": "fecha", "type": "TIMESTAMP"},
  {"name": "duracion", "type": "INT64"},
  {"name": "estado", "type": "STRING"},
  {"name": "zona_involucrada", "type": "STRING"}
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

#firestore database in native mode
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}