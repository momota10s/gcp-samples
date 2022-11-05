/*
GKEヘルスチェックで利用するcloud functionの定義
*/

data "archive_file" "gke_healthcheck" {
  source_dir  = "${path.module}/src/gke-healthcheck"
  output_path = "${path.module}/src/archive/gke-healthcheck/src.zip"
  type        = "zip"
}

resource "google_storage_bucket_object" "gke_healthcheck" {
  name   = "packages/gke-healthcheck/src.${data.archive_file.gke_healthcheck.output_md5}.zip"
  bucket = var.gcf_bucket_name
  source = data.archive_file.gke_healthcheck.output_path
}

resource "google_service_account" "gke_healthcheck" {
  account_id   = "gke-healthcheck"
  display_name = "gke-healthcheck"
}

resource "google_cloudfunctions_function" "gke_healthcheck" {
  name                  = "gke-healthcheck"
  runtime               = "python39"
  source_archive_bucket = var.gcf_bucket_name
  source_archive_object = google_storage_bucket_object.gke_healthcheck.name
  available_memory_mb   = 256
  timeout               = 60
  entry_point           = "run"
  max_instances         = 3000
  service_account_email = google_service_account.gke_healthcheck.email
  environment_variables = {
    "ENV"              = var.env,
    "GKE_CONSOLE_LINK" = var.gke_console_link,
    "SLACK_WEBHOOK"    = var.slack_webhook
  }
  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.gke_healthcheck.name
  }
  labels = {
    terraform = true
  }
}


/*
GKEヘルスチェックを定期実行するためのスケジューラーとpubsubの定義
*/

resource "google_pubsub_topic" "gke_healthcheck" {
  name = "gke-healthcheck"
  labels = {
    terraform = true
  }
}

resource "google_cloud_scheduler_job" "gke_healthcheck" {
  name      = "gke-healthcheck"
  schedule  = "*/5 * * * *"
  time_zone = "Asia/Tokyo"

  pubsub_target {
    topic_name = google_pubsub_topic.gke_healthcheck.id
    data       = base64encode("check gke status")
  }
  retry_config {
    max_backoff_duration = "3600s"
    max_doublings        = 5
    max_retry_duration   = "0s"
    min_backoff_duration = "5s"
    retry_count          = 0
  }
}


