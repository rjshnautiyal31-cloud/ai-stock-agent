# =================-------------------------------------------------------------
# GCP Secret Manager Secret Placeholder
# =================-------------------------------------------------------------
resource "google_secret_manager_secret" "alpha_vantage_key" {
  secret_id = "alpha-vantage-api-key"

  replication {
    auto {}
  }
}

# =================-------------------------------------------------------------
# Dedicated Runtime Service Account for Alpha Vantage MCP Server
# =================-------------------------------------------------------------
resource "google_service_account" "mcp_runner" {
  account_id   = "alphavantage-mcp-runner"
  display_name = "Alpha Vantage MCP Runner"
  description  = "Service account used as the runtime identity of the Alpha Vantage MCP Cloud Run service"
}

# Grant the runner service account access to retrieve ONLY the Alpha Vantage API key secret
resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  secret_id = google_secret_manager_secret.alpha_vantage_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.mcp_runner.email}"
}

# =================-------------------------------------------------------------
# Google Cloud Run v2 Service running the MCP Server
# =================-------------------------------------------------------------
resource "google_cloud_run_v2_service" "mcp_service" {
  name     = "alphavantage-mcp-server"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.mcp_runner.email

    containers {
      image = var.image_uri

      ports {
        container_port = 8080
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      # Inject the project ID environment variable so the client can implicitly resolve ADC project
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
    }
  }

  # Ensure Secret Manager IAM policy is active before Cloud Run services are spun up
  depends_on = [
    google_secret_manager_secret_iam_member.secret_accessor
  ]
}

# =================-------------------------------------------------------------
# Cloud Run IAM Permissions for Public Invocation (Cognitive Layer Integration)
# =================-------------------------------------------------------------
resource "google_cloud_run_v2_service_iam_member" "mcp_invoker" {
  name     = google_cloud_run_v2_service.mcp_service.name
  location = google_cloud_run_v2_service.mcp_service.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
