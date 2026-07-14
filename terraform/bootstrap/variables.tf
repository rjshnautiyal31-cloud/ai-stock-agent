variable "project_id" {
  type        = string
  description = "The GCP Project ID where resources will be bootstrapped."
  default     = "fabled-ruler-363118"
}

variable "region" {
  type        = string
  description = "The default region for provisioning resources."
  default     = "us-central1"
}

variable "github_repository" {
  type        = string
  description = "The GitHub repository in 'owner/repo' format (e.g., 'username/repo') permitted to assume the CI/CD role."
}

variable "tf_state_bucket_name" {
  type        = string
  description = "The name of the GCS bucket to create for remote Terraform state storage."
  default     = "fabled-ruler-363118-tfstate"
}
