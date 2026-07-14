output "mcp_service_url" {
  value       = google_cloud_run_v2_service.mcp_service.uri
  description = "The dynamically resolved URI of the Alpha Vantage MCP Cloud Run service."
}
