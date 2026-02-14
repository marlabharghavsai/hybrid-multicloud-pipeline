############################################################
# Pub/Sub Topic
############################################################
resource "google_pubsub_topic" "topic" {
  name = "localstack-events"
}

############################################################
# Cloud SQL Instance
############################################################
resource "google_sql_database_instance" "db_instance" {
  name             = "pipeline-sql-instance"
  database_version = "POSTGRES_13"
  region           = var.gcp_region

  settings {
    tier = "db-f1-micro"
  }

  deletion_protection = false
}

############################################################
# Database
############################################################
resource "google_sql_database" "database" {
  name     = "pipelinedb"
  instance = google_sql_database_instance.db_instance.name
}

############################################################
# DB USER
############################################################
resource "google_sql_user" "db_user" {
  name     = "pipelineuser"
  instance = google_sql_database_instance.db_instance.name
  password = "pipelinepass123"
}

############################################################
# CUSTOM SERVICE ACCOUNT
############################################################
resource "google_service_account" "function_sa" {
  account_id   = "processor-function-sa"
  display_name = "Processor Function Service Account"
}

############################################################
# STORAGE BUCKET
############################################################
resource "google_storage_bucket" "function_bucket" {
  name                        = "${var.gcp_project_id}-function-bucket"
  location                    = var.gcp_region
  force_destroy               = true
  uniform_bucket_level_access = true
}

############################################################
# FUNCTION ZIP
############################################################
resource "google_storage_bucket_object" "function_zip" {
  name   = "processor-function.zip"
  bucket = google_storage_bucket.function_bucket.name
  source = "../src/processor_function/function.zip"
}

############################################################
# CLOUD FUNCTION GEN2 (FINAL FIXED VERSION)
############################################################
resource "google_cloudfunctions2_function" "processor" {

  name     = "processor-function"
  location = var.gcp_region

  ##################################################
  # BUILD CONFIG
  ##################################################
  build_config {
    runtime     = "python310"
    entry_point = "process_event"

    source {
      storage_source {
        bucket = google_storage_bucket.function_bucket.name
        object = google_storage_bucket_object.function_zip.name
      }
    }
  }

  ##################################################
  # SERVICE CONFIG
  ##################################################
  service_config {
    available_memory = "256M"
    timeout_seconds  = 60

    # ⭐ FORCE CUSTOM SERVICE ACCOUNT
    service_account_email = google_service_account.function_sa.email

    environment_variables = {
      DYNAMODB_ENDPOINT = "http://host.docker.internal:4566"
      DB_USER           = "pipelineuser"
      DB_PASS           = "pipelinepass123"
      DB_NAME           = "pipelinedb"
      DB_INSTANCE       = google_sql_database_instance.db_instance.connection_name
    }
  }

  ##################################################
  # ⭐ EVENT TRIGGER (CRITICAL FIX)
  ##################################################
  event_trigger {
    trigger_region = var.gcp_region
    event_type     = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic   = google_pubsub_topic.topic.id

    # ⭐ THIS LINE FIXES THE COMPUTE SA ERROR
    service_account_email = google_service_account.function_sa.email
  }

  depends_on = [
    google_sql_database.database,
    google_sql_user.db_user
  ]
}
