import os
import logging
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from src.agent_runtime.agent import AlphaVantageAgentRuntime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Resolve the backend MCP server URL from environment variables passed by Terraform
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL")

async def chat_endpoint(request):
    """
    Exposes a POST /chat REST endpoint to interact with the grounded stock agent.
    Expects: { "prompt": "..." }
    Returns: { "response": "..." }
    """
    if not MCP_SERVER_URL:
        logger.error("MCP_SERVER_URL environment variable is not configured on this container.")
        return JSONResponse({"error": "MCP_SERVER_URL environment variable is not configured on this container."}, status_code=500)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid or missing JSON payload."}, status_code=400)

    prompt = body.get("prompt", "").strip()
    if not prompt:
        return JSONResponse({"error": "Field 'prompt' is required and must not be empty."}, status_code=400)

    logger.info(f"Cognitive Layer received chat prompt: '{prompt}'")
    
    # Initialize runtime dynamically pointing to the live Cloud Run backend
    runtime = AlphaVantageAgentRuntime(mcp_server_url=MCP_SERVER_URL)
    try:
        # 1. Connect to live MCP over SSE, run handshake, and load tools
        await runtime.initialize_agent()
        
        # 2. Run chat query using Vertex AI Gemini ADK LlmAgent
        response = await runtime.run_chat(prompt)
        
        # 3. Return JSON response payload
        return JSONResponse({"response": response})
    except Exception as e:
        logger.error(f"Error during agent runtime execution: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        # 4. Safely clean up and close the SSE active stack
        await runtime.close()

async def health_endpoint(request):
    """Simple container health check endpoint."""
    return JSONResponse({"status": "healthy"})

# Build Starlette App
app = Starlette(
    routes=[
        Route("/chat", chat_endpoint, methods=["POST"]),
        Route("/health", health_endpoint, methods=["GET"])
    ]
)
