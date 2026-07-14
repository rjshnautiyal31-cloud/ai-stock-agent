# ------------------------------------------------------------------------------
# Terraform Outputs for GitHub Actions Configuration
# ------------------------------------------------------------------------------

output "gcs_state_bucket" {
  value       = google_storage_bucket.tf_state.name
  description = "The name of the GCS bucket created for remote Terraform state storage."
}

output "workload_identity_provider_name" {
  value       = google_iam_workload_identity_pool_provider.github_provider.name
  description = "The full resource name of the Workload Identity Provider to use in GitHub Actions authentication (use in 'workload_identity_provider' field)."
}

output "github_deployer_service_account_email" {
  value       = google_service_account.github_deployer.email
  description = "The email of the dedicated CI/CD execution service account (use in 'service_account' field)."
}
