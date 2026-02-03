terraform {
  backend "gcs" {
    bucket  = "tfstate_data_project_2_jamagece"
    prefix  = "terraform/state" 
  }
}