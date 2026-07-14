# =================-------------------------------------------------------------
# Declarative Cognitive Layer: Vertex AI (Dialogflow CX) Agent
# =================-------------------------------------------------------------
resource "google_dialogflow_cx_agent" "alphavantage_agent" {
  display_name          = "alphavantage-stock-agent"
  location              = var.region
  default_language_code = "en"
  time_zone             = "America/New_York"
  description           = "Cognitive Alpha Vantage financial analyst agent powered by the backend MCP server hosted at ${google_cloud_run_v2_service.mcp_service.uri}"

  enable_stackdriver_logging = true
  enable_spell_correction    = true

  speech_to_text_settings {
    enable_speech_adaptation = true
  }
}
