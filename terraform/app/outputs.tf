output "mcp_service_url" {
  value       = google_cloud_run_v2_service.mcp_service.uri
  description = "The dynamically resolved URI of the Alpha Vantage MCP Cloud Run service."
}

output "ge_app_id" {
  value       = google_discovery_engine_chat_engine.alphavantage_ge_app.id
  description = "The resource ID of the newly provisioned Gemini Enterprise (GE) App / Chat Engine."
}

output "ge_app_underlying_agent" {
  value       = google_discovery_engine_chat_engine.alphavantage_ge_app.chat_engine_metadata[0].dialogflow_agent
  description = "The resource ID of the auto-generated Dialogflow CX Agent powering this GE App."
}
