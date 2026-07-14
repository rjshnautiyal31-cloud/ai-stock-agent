variable "project_id" {
  type        = string
  description = "The GCP Project ID where application resources will be deployed."
  default     = "fabled-ruler-363118"
}

variable "region" {
  type        = string
  description = "The default GCP region for the application."
  default     = "us-central1"
}

variable "image_uri" {
  type        = string
  description = "The container image URI for the MCP server Cloud Run service."
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "github_repository" {
  type        = string
  description = "The GitHub repository in 'owner/repo' format (e.g., 'username/repo') permitted to assume the CI/CD role."
}
