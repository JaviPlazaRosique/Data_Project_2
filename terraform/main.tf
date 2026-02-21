terraform {
  backend "gcs" {
    bucket  = "tfstate_data_project_2_jamagece"
    prefix  = "terraform/state" 
  }
}

resource "google_project_service" "activar_servicios_proyecto" {
  for_each = toset(var.servicios_gcp)
  project = var.project_id
  service = each.value
  disable_on_destroy = false
}

resource "google_compute_network" "vpc_monitoreo_menores" {
  name = "vpc-monitoreo-menores"
  project = var.project_id
  depends_on = [google_project_service.activar_servicios_proyecto]
}

resource "google_compute_global_address" "rango_ip_monitoreo_menores" {
  name = "rango-ip-monitoreo-menores"
  purpose = "VPC_PEERING"
  address_type = "INTERNAL"
  network = google_compute_network.vpc_monitoreo_menores.id
  address = "10.0.0.0"
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
  depends_on = [google_project_service.activar_servicios_proyecto]
}

resource "google_storage_bucket" "dataflow-temp" {
  name          = "dataflow-temp-${var.project_id}"
  location      = var.region
  force_destroy = false
  storage_class = "STANDARD"
  depends_on = [google_project_service.activar_servicios_proyecto]
}

resource "google_pubsub_topic" "topic-ubicacion" {
  name = "topic-ubicacion"
  depends_on = [google_project_service.activar_servicios_proyecto]
}

resource "google_pubsub_subscription" "topic-ubicacion-sub" {
  name  = "${google_pubsub_topic.topic-ubicacion.name}-sub"
  topic = google_pubsub_topic.topic-ubicacion.name
}

resource "google_pubsub_topic" "topic-eventos" {
  name = "topic-eventos"
  depends_on = [google_project_service.activar_servicios_proyecto]
}

resource "google_pubsub_subscription" "topic-eventos-sub" {
  name  = "${google_pubsub_topic.topic-eventos.name}-sub"
  topic = google_pubsub_topic.topic-eventos.name
}


resource "google_pubsub_topic" "topic-user-notification" {
  name = "user-notification"
  depends_on = [google_project_service.activar_servicios_proyecto]
}

resource "google_sql_database_instance" "postgres_instance" {
  name = "monitoreo-menores"
  region = var.region
  database_version = "POSTGRES_17"
  deletion_protection = false
  settings {
    edition = "ENTERPRISE"
    tier = "db-f1-micro"
    availability_type = "ZONAL"
    disk_size = 100

    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc_monitoreo_menores.id
    }
    database_flags {
      name = "cloudsql.logical_decoding"
      value = "on"
    }
  }
  lifecycle {
    prevent_destroy = true
  }
  depends_on = [
    google_service_networking_connection.private_vpc_connection,
    google_project_service.activar_servicios_proyecto
  ]
}

resource "random_password" "contraseña-monitoreo-menores" {
  length = 16
  special = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "random_password" "api_key" {
  length = 32
  special = false
}

resource "random_password" "contr_usuario_datastream" {
  length = 32
  special = false
}

resource "google_sql_user" "postgres_user" {
  name = "admin"
  instance = google_sql_database_instance.postgres_instance.name
  password = random_password.contraseña-monitoreo-menores.result
}

resource "google_sql_database" "menores_db" {
  name = "menores_db"
  instance = google_sql_database_instance.postgres_instance.name
}

resource "google_bigquery_dataset" "monitoreo_dataset" {
  dataset_id = "monitoreo_dataset"
  project = var.project_id
  location = var.region
  depends_on = [google_project_service.activar_servicios_proyecto]
}

resource "google_bigquery_table" "menores" {
  dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
  table_id = "menores"

  schema = <<EOF
[
  {"name": "id", "type": "STRING"},
  {"name": "id_adulto", "type": "STRING"},
  {"name": "nombre", "type": "STRING"},
  {"name": "apellidos", "type": "STRING"},
  {"name": "fecha_nacimiento", "type": "STRING"},
  {"name": "direccion", "type": "STRING"},
  {"name": "discapacidad", "type": "BOOLEAN"}

]
EOF
  table_constraints {
    primary_key {
      columns = ["id"]
    }
    foreign_keys {
      name = "fk_menor_adulto"
      referenced_table {
        project_id = var.project_id
        dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
        table_id = google_bigquery_table.adultos.table_id
      }
      column_references {
        referencing_column = "id_adulto"
        referenced_column = "id"
      }
    }
  }
  lifecycle {
    ignore_changes = [schema]
  }
}

resource "google_bigquery_table" "adultos" {
  dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
  table_id   = "adultos"

  schema = <<EOF
[
  {"name": "id", "type": "STRING"},
  {"name": "nombre", "type": "STRING"},
  {"name": "apellidos", "type": "STRING"}
]
EOF
  table_constraints {
    primary_key {
      columns = ["id"]
    }
  }
  lifecycle {
    ignore_changes = [schema]
  }
}

resource "google_bigquery_table" "historico_notificaciones" {
  dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
  table_id   = "historico_notificaciones"
  time_partitioning {
    type  = "DAY"
    field = "fecha"
  }
  schema = <<EOF
[ 
  {"name": "id_menor", "type": "STRING"},
  {"name": "nombre_menor", "type": "STRING"},
  {"name": "latitud", "type": "FLOAT"},
  {"name": "longitud", "type": "FLOAT"},
  {"name": "fecha", "type": "TIMESTAMP"},
  {"name": "estado", "type": "STRING"}
]
EOF
}

resource "google_bigquery_table" "zonas-restringidas" {
  dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
  table_id   = "zonas_restringidas"

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
  table_constraints {
    primary_key {
      columns = ["id"]
    }
    foreign_keys {
      name = "fk_zona_menor"
      referenced_table {
        project_id = var.project_id
        dataset_id = google_bigquery_dataset.monitoreo_dataset.dataset_id
        table_id = google_bigquery_table.menores.table_id
      }
      column_references {
        referencing_column = "id_menor"
        referenced_column = "id"
      }
    }
  }
  lifecycle {
    ignore_changes = [schema]
  }
}

resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
  depends_on = [google_project_service.activar_servicios_proyecto]
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
  depends_on = [google_project_service.activar_servicios_proyecto]
}

locals {
  api_hash = sha1(join("", [for f in fileset("${path.module}/../api", "**") : filesha1("${path.module}/../api/${f}")]))
  web_hash = sha1(join("", [for f in fileset("${path.module}/../web", "**") : filesha1("${path.module}/../web/${f}")]))
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

resource "google_cloud_run_v2_service" "api_cloud_run" {
  name = "api-cloud-run"
  location = var.region
  deletion_protection = false
  template {
    service_account = google_service_account.api_cloud_run.email
    containers {
      image = docker_registry_image.imagen_api_push.name
      volume_mounts {
        name = "cloudsql"
        mount_path = "/cloudsql"
      }
      ports {
        container_port = 8000
      }
      startup_probe {
        initial_delay_seconds = 10
        timeout_seconds  = 5
        period_seconds = 10
        failure_threshold = 24
        tcp_socket {
          port = 8000
        }
      }
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
      env {
        name = "BUCKET_FOTOS"
        value = google_storage_bucket.bucket-menores.name
      }
      env {
        name = "API_KEY"
        value = random_password.api_key.result
      }
      env {
        name = "CONTR_USUARIO_DATASTREAM"
        value = random_password.contr_usuario_datastream.result
      }
      env {
        name = "PYTHONUNBUFFERED"
        value = "1"
      }
    }
    vpc_access {
      network_interfaces {
        network = google_compute_network.vpc_monitoreo_menores.id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.postgres_instance.connection_name]
      }
    }
  }
  depends_on = [google_project_service.activar_servicios_proyecto]
}

resource "local_file" "env_generadores" {
  filename = "${path.module}/../Generadores/.env"
  content  = <<-EOT
    BUCKET_FOTOS = ${google_storage_bucket.bucket-menores.name}
    URL_API = ${google_cloud_run_v2_service.api_cloud_run.uri}
    API_KEY = ${random_password.api_key.result}
  EOT
}

resource "docker_image" "imagen_web" {
  name = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.repo_artifact.name}/web:${local.web_hash}"
  build {
    context = "../web/"
    dockerfile = "Dockerfile"
  }
}

resource "docker_registry_image" "imagen_web_push" {
  name = docker_image.imagen_web.name
  keep_remotely = true
}

resource "google_cloud_run_v2_service" "web_cloud_run" {
  name = "web-cloud-run"
  location = var.region
  deletion_protection = false
  template {
    service_account = google_service_account.web_cloud_run.email
    containers {
      image = docker_registry_image.imagen_web_push.name
      ports {
        container_port = 8080
      }
      startup_probe {
        initial_delay_seconds = 10
        timeout_seconds = 5
        period_seconds = 10
        failure_threshold = 24
        tcp_socket {
          port = 8080
        }
      }
      env {
        name = "STREAMLIT_SERVER_PORT"
        value = "8080"
      }
      env {
        name = "STREAMLIT_SERVER_HEADLESS"
        value = "true"
      }
      env {
        name = "STREAMLIT_SERVER_ENABLECORS"
        value = "false"
      }
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
        name = "BUCKET_FOTOS"
        value = google_storage_bucket.bucket-menores.name
      }
    }
    vpc_access {
      network_interfaces {
        network = google_compute_network.vpc_monitoreo_menores.id
      }
      egress = "PRIVATE_RANGES_ONLY"
    }
  }
  depends_on = [
    docker_registry_image.imagen_web_push,
    google_project_service.activar_servicios_proyecto
  ]
}

resource "null_resource" "lanzar_dataflow" {
  triggers = {
    password = random_password.contraseña-monitoreo-menores.result
    db_host  = google_sql_database_instance.postgres_instance.private_ip_address
  }

  provisioner "local-exec" {
    command = <<EOT
    python ../Dataflow/pipeline.py --project_id=${var.project_id} --ubicacion_pubsub_subscription_name=${google_pubsub_topic.topic-ubicacion.name}-sub --bigquery_dataset=${google_bigquery_dataset.monitoreo_dataset.dataset_id} --historico_notificaciones_bigquery_table=${google_bigquery_table.historico_notificaciones.table_id} --db_host=${google_sql_database_instance.postgres_instance.private_ip_address} --db_user=${google_sql_user.postgres_user.name} --db_pass="${random_password.contraseña-monitoreo-menores.result}" --runner=DataflowRunner --region=${var.region} --network=${google_compute_network.vpc_monitoreo_menores.name} --subnetwork=regions/${var.region}/subnetworks/${google_compute_network.vpc_monitoreo_menores.name} --job_name=pipeline-monitoreo-menores --requirements_file=../Dataflow/requirements.txt
    EOT
  }

  depends_on = [
    google_sql_user.postgres_user,
    google_sql_database.menores_db,
    google_service_networking_connection.private_vpc_connection
  ]
}
resource "google_datastream_connection_profile" "conexion_origen_datastream" {
  display_name = "Conexión de origen para Datastream (PostgreSQL)"
  location = var.region
  connection_profile_id = "conexion-sql-origen-datastream"
  postgresql_profile {
    hostname = google_compute_instance.proxy_datastream.network_interface[0].network_ip
    port = 5432
    username = google_sql_user.postgres_user.name
    password = google_sql_user.postgres_user.password
    database = google_sql_database.menores_db.name
  }
  private_connectivity {
    private_connection = google_datastream_private_connection.conexion_privada_datastream.id
  }
  depends_on = [
    google_project_service.activar_servicios_proyecto,
    time_sleep.esperar_instalacion_proxy
  ]
}

resource "google_datastream_connection_profile" "conexion_destino_datastream" {
  display_name = "Conexión de destino para Datastream (BigQuery)"
  location = var.region
  connection_profile_id = "conexion-bq-destino-datastream"
  bigquery_profile {
    
  }
  depends_on = [google_project_service.activar_servicios_proyecto]
}

resource "google_datastream_private_connection" "conexion_privada_datastream" {
  display_name = "Conexión privada para Datastream"
  location = var.region
  private_connection_id = "conexion-psc-datastream"
  vpc_peering_config {
    vpc = google_compute_network.vpc_monitoreo_menores.id
    subnet = "10.10.0.0/29"
  }
  depends_on = [google_project_service.activar_servicios_proyecto]
}

resource "google_datastream_stream" "sql_bq" {
  display_name = "Conexión PostgreSQL con BigQuery"
  location = var.region
  stream_id = "sql-bq"
  desired_state = "RUNNING"
  backfill_all {}
  source_config {
    source_connection_profile = google_datastream_connection_profile.conexion_origen_datastream.id
    postgresql_source_config {
      replication_slot = "datastream_slot"
      publication = "datastream_publication"
      include_objects {
        postgresql_schemas {
          schema = "public"
          postgresql_tables {
            table = "adultos"
            postgresql_columns {column = "id"}
            postgresql_columns {column = "nombre"}
            postgresql_columns {column = "apellidos"}
          }
          postgresql_tables {
            table = "menores"
            postgresql_columns {column = "id"}
            postgresql_columns {column = "id_adulto"}
            postgresql_columns {column = "nombre"}
            postgresql_columns {column = "apellidos"}
            postgresql_columns {column = "fecha_nacimiento"}
            postgresql_columns {column = "direccion"}
            postgresql_columns {column = "discapacidad"}
          }
          postgresql_tables {
            table = "zonas_restringidas"
            postgresql_columns {column = "id"}
            postgresql_columns {column = "id_menor"}
            postgresql_columns {column = "nombre"}
            postgresql_columns {column = "latitud"}
            postgresql_columns {column = "longitud"}
            postgresql_columns {column = "radio_peligro"}
            postgresql_columns {column = "radio_advertencia"}
          }
        }
      }
    }
  }
  destination_config {
    destination_connection_profile = google_datastream_connection_profile.conexion_destino_datastream.id
    bigquery_destination_config {
      single_target_dataset {
        dataset_id = "${var.project_id}:${google_bigquery_dataset.monitoreo_dataset.dataset_id}"
      }
    }
  }
  depends_on = [time_sleep.esperar_arranque_api]
}

resource "google_compute_firewall" "permitir_datastream_proxy" {
  name = "permitir-datastream-proxy"
  network = google_compute_network.vpc_monitoreo_menores.id
  allow {
    protocol = "tcp"
    ports = ["5432"]
  }
  source_ranges = ["10.10.0.0/29"] 
}

data "google_compute_image" "debian" {
  family = "debian-12"
  project = "debian-cloud"
}

resource "google_compute_instance" "proxy_datastream" {
  name = "proxy-datastream-cloudsql"
  machine_type = "e2-micro"
  zone = "${var.region}-a" 

  boot_disk {
    initialize_params {
      image = data.google_compute_image.debian.id
    }
  }
  network_interface {
    network = google_compute_network.vpc_monitoreo_menores.id
    access_config {}
  }
  metadata_startup_script = <<-EOF
    #! /bin/bash
    apt-get update
    apt-get install -y haproxy
    
    cat <<EOT > /etc/haproxy/haproxy.cfg
    global
        daemon
        maxconn 256
    defaults
        mode tcp
        timeout connect 5000ms
        timeout client 50000ms
        timeout server 50000ms
    frontend postgres_in
        bind *:5432
        default_backend postgres_out
    backend postgres_out
        server cloudsql ${google_sql_database_instance.postgres_instance.private_ip_address}:5432 check
    EOT
    
    systemctl restart haproxy
  EOF
  depends_on = [google_compute_network.vpc_monitoreo_menores]
}

resource "time_sleep" "esperar_instalacion_proxy" {
  depends_on = [google_compute_instance.proxy_datastream]
  create_duration = "120s"
}

resource "time_sleep" "esperar_arranque_api" {
  depends_on = [google_cloud_run_v2_service.api_cloud_run]
  create_duration = "60s"
}