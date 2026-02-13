############################
# Pub/Sub Topic
############################
resource "google_pubsub_topic" "topic" {
  name = "localstack-events"
}

############################
# Cloud SQL Instance
############################
resource "google_sql_database_instance" "db_instance" {
  name             = "pipeline-sql-instance"
  database_version = "POSTGRES_13"
  region           = var.gcp_region

  settings {
    tier = "db-f1-micro"
  }

  deletion_protection = false
}

############################
# Database
############################
resource "google_sql_database" "database" {
  name     = "pipelinedb"
  instance = google_sql_database_instance.db_instance.name
}
