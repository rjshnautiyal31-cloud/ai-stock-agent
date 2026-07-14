# ------------------------------------------------------------------------------
# GCS Bucket for Remote Terraform State Storage
# ------------------------------------------------------------------------------
resource "google_storage_bucket" "tf_state" {
  name                        = var.tf_state_bucket_name
  location                    = var.region
  force_destroy               = false
  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 5
    }
  }
}

# ------------------------------------------------------------------------------
# Workload Identity Federation (OIDC) for GitHub Actions
# ------------------------------------------------------------------------------
resource "google_iam_workload_identity_pool" "github_pool" {
  workload_identity_pool_id = "github-actions-pool"
  display_name              = "GitHub Actions Pool"
  description               = "Workload Identity Pool for GitHub Actions GitOps pipeline baseline"
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.github_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions-provider"
  display_name                       = "GitHub Actions Provider"
  description                        = "Workload Identity Provider mapped to GitHub OIDC"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  attribute_condition = "assertion.repository == '${var.github_repository}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# ------------------------------------------------------------------------------
# Dedicated CI/CD Service Account & Federation Permissions
# ------------------------------------------------------------------------------
resource "google_service_account" "github_deployer" {
  account_id   = "github-actions-deployer"
  display_name = "GitHub Actions CI/CD Deployer"
  description  = "Service account assumed by GitHub Actions via OIDC Workload Identity Federation"
}

# Strict IAM Policy binding restricting assumption only to the designated GitHub repository
resource "google_service_account_iam_member" "workload_identity_binding" {
  service_account_id = google_service_account.github_deployer.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github_pool.name}/attribute.repository/${var.github_repository}"
}

# ------------------------------------------------------------------------------
# Project-Level IAM Permissions for Deployments (Least Privilege)
# ------------------------------------------------------------------------------
locals {
  project_roles = [
    "roles/run.admin",                       # Manage Cloud Run instances
    "roles/secretmanager.admin",             # Manage Secret Manager objects/secrets
    "roles/discoveryengine.admin",           # Manage Vertex AI Agent engines / Search & Conversation
    "roles/iam.serviceAccountUser",          # User of runtime service accounts
    "roles/iam.serviceAccountAdmin",         # Create/manage runtime service accounts
    "roles/resourcemanager.projectIamAdmin", # Assign roles/permissions to runtime service accounts
    "roles/dialogflow.admin"                 # Create and manage conversational agents (Dialogflow CX)
  ]
}

resource "google_project_iam_member" "deployer_project_roles" {
  for_each = toset(local.project_roles)
  project  = var.project_id
  role     = each.key
  member   = "serviceAccount:${google_service_account.github_deployer.email}"
}

# Grant the CI/CD deployer full admin rights over the newly created TF state bucket
resource "google_storage_bucket_iam_member" "state_bucket_admin" {
  bucket = google_storage_bucket.tf_state.name
  role   = "roles/storage.admin"
  member = "serviceAccount:${google_service_account.github_deployer.email}"
}
