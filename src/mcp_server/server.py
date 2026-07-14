import logging
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse

from src.mcp_server.secrets import GCPSecretManagerClient
from src.mcp_server.toolkit import AlphaVantageToolKit

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class MCPServerApplication:
    """
    Factory for launching the Alpha Vantage Model Context Protocol (MCP) Server.
    Integrates GCP Secret Manager, Alpha Vantage Toolkit, and FastMCP.
    """
    @classmethod
    def create_app(cls) -> Starlette:
        """
        Creates and returns the Starlette application running over SSE.
        """
        logger.info("Initializing MCPServerApplication factory...")
        try:
            # 1. Initialize GCP Secret Manager Client
            secret_client = GCPSecretManagerClient()
            
            # 2. Fetch the Alpha Vantage API key from Secret Manager
            logger.info("Fetching 'alpha-vantage-api-key' from Secret Manager...")
            api_key = secret_client.get_secret("alpha-vantage-api-key")
            
            # 3. Instantiate the Alpha Vantage Toolkit
            toolkit = AlphaVantageToolKit(api_key=api_key)
            
            # 4. Initialize FastMCP (Passing host="0.0.0.0" to disable the localhost-only DNS guard on Cloud Run)
            logger.info("Initializing FastMCP Server...")
            mcp = FastMCP(
                "Alpha Vantage Real-time Stock Server",
                host="0.0.0.0",
                dependencies=["requests", "google-cloud-secret-manager", "google-auth", "starlette", "uvicorn"]
            )
            
            # Register the stock quote tool
            @mcp.tool(name="get_stock_quote", description="Fetch real-time stock pricing metrics from Alpha Vantage for a given ticker symbol.")
            def get_stock_quote(symbol: str) -> dict:
                """
                Retrieves current market price, open, high, low, volume, latest trading day, previous close, change, and change percent.
                """
                return toolkit.get_stock_quote(symbol)

            # 5. Generate the Starlette application over SSE transport
            logger.info("Generating Starlette ASGI app over Server-Sent Events (SSE) transport...")
            # sse_app() returns the Starlette-based ASGI application with SSE transport
            starlette_app = mcp.sse_app()
            
            # 6. Add a traditional REST GET /quote route for Dialogflow CX integration
            async def get_quote_rest(request):
                symbol = request.query_params.get("symbol", "").strip().upper()
                if not symbol:
                    return JSONResponse({"error": "Symbol query parameter is required"}, status_code=400)
                try:
                    quote = toolkit.get_stock_quote(symbol)
                    return JSONResponse(quote)
                except Exception as e:
                    return JSONResponse({"error": str(e)}, status_code=500)
                    
            starlette_app.add_route("/quote", get_quote_rest, methods=["GET"])
            
            logger.info("MCPServerApplication ASGI app created successfully.")
            return starlette_app
            
        except Exception as e:
            logger.error(f"Critical error during MCPServerApplication creation: {e}")
            raise
