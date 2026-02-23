terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.6.2"
    }
  }
}

provider "google" {
    project = var.project_id
    region = var.region
    user_project_override = true
}

provider "random" {}

data "google_client_config" "default" {}

provider "docker" {
  registry_auth {
    address  = "${var.region}-docker.pkg.dev"
    username = "oauth2accesstoken"
    password = data.google_client_config.default.access_token
  }

provider "google-beta" {
    project = var.project_id
    region = var.region
    user_project_override = true
}