# =================-------------------------------------------------------------
# 1. Backing Discovery Engine Data Store (Required for Generative Chat Engines)
# =================-------------------------------------------------------------
resource "google_discovery_engine_data_store" "alphavantage_datastore" {
  provider          = google-beta
  location          = "global"
  data_store_id     = "alphavantage-agent-datastore"
  display_name      = "Alpha Vantage Agent Data Store"
  industry_vertical = "GENERIC"
  content_config    = "NO_CONTENT"
  solution_types    = ["SOLUTION_TYPE_CHAT"]

  lifecycle {
    ignore_changes = [
      advanced_site_search_config
    ]
  }
}

# =================-------------------------------------------------------------
# 2. Declarative GE App (Vertex AI Generative Chat Engine)
# =================-------------------------------------------------------------
resource "google_discovery_engine_chat_engine" "alphavantage_ge_app" {
  provider          = google-beta
  engine_id         = "alphavantage-stock-agent"
  collection_id     = "default_collection"
  location          = google_discovery_engine_data_store.alphavantage_datastore.location
  display_name      = "alphavantage-stock-agent"
  industry_vertical = "GENERIC"
  data_store_ids    = [google_discovery_engine_data_store.alphavantage_datastore.data_store_id]

  chat_engine_config {
    agent_creation_config {
      business              = "Alpha Vantage"
      default_language_code = "en"
      time_zone             = "America/New_York"
    }
  }

  depends_on = [
    google_discovery_engine_data_store.alphavantage_datastore
  ]
}

# =================-------------------------------------------------------------
# 3. Declarative Conversational API Tool: Map Cloud Run REST Endpoint to the GE App
# =================-------------------------------------------------------------
resource "google_dialogflow_cx_tool" "alphavantage_tool" {
  provider = google-beta
  # Extract the auto-created agent ID directly from the GE App metadata
  parent       = google_discovery_engine_chat_engine.alphavantage_ge_app.chat_engine_metadata[0].dialogflow_agent
  display_name = "AlphaVantageTool"
  description  = "Retrieves live financial quotes, trading metrics, and percentage change for any stock symbol (e.g. AAPL, GOOG)."

  open_api_spec {
    text_schema = <<EOF
{
  "openapi": "3.0.0",
  "info": {
    "title": "Alpha Vantage Proxy API",
    "version": "1.0.0",
    "description": "REST endpoint exposing real-time stock quotes from Alpha Vantage."
  },
  "servers": [
    {
      "url": "${google_cloud_run_v2_service.mcp_service.uri}"
    }
  ],
  "paths": {
    "/quote": {
      "get": {
        "operationId": "getStockQuote",
        "summary": "Fetches current trading metrics and daily price changes for a given stock symbol",
        "parameters": [
          {
            "name": "symbol",
            "in": "query",
            "description": "The stock ticker symbol (e.g. AAPL, GOOG)",
            "required": true,
            "schema": {
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "description": "Successful retrieval of stock quote",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object"
                }
              }
            }
          }
        }
      }
    }
  }
}
EOF
  }
}

# =================-------------------------------------------------------------
# 4. Declarative Conversational Generative Playbook in GE App
# =================-------------------------------------------------------------
resource "google_dialogflow_cx_playbook" "stock_analyst" {
  provider = google-beta
  # Extract parent agent ID directly from the GE App metadata
  parent       = google_discovery_engine_chat_engine.alphavantage_ge_app.chat_engine_metadata[0].dialogflow_agent
  display_name = "StockAnalystSpecialist"
  goal         = "Greet the user, identify stock tickers, invoke the AlphaVantageTool to get live quote metrics, and summarize findings in an elegant and professional financial format."

  referenced_tools = [
    google_dialogflow_cx_tool.alphavantage_tool.id
  ]

  instruction {
    steps {
      text = "Greet the user warmly and introduce yourself as a sophisticated, real-time stock assistant."
    }
    steps {
      text = "When the user asks for stock information, prices, tickers, or performance, extract the ticker symbol."
    }
    steps {
      text = "Always call the AlphaVantageTool's getStockQuote method, passing the parsed stock symbol as the query parameter."
    }
    steps {
      text = "Evaluate the retrieved metrics, including price, high, low, previous close, and percentage daily change."
    }
    steps {
      text = "Formulate a clear, structured response summarizing the daily performance, formatting numbers cleanly, and displaying changes clearly."
    }
  }
}
