import asyncio
import logging
from typing import Optional
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, SseConnectionParams
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class AlphaVantageAgentRuntime:
    """
    Cognitive Layer Engine using Object-Oriented Design.
    Initializes a Vertex AI ADK LlmAgent dynamically bound to the Alpha Vantage MCP Cloud Run server over SSE.
    """
    def __init__(self, mcp_server_url: str) -> None:
        if not mcp_server_url:
            raise ValueError("MCP Server URL must not be empty.")
        # Ensure url ends with /sse (which Starlette uses for FastMCP transport)
        self.mcp_server_url = mcp_server_url.rstrip("/")
        if not self.mcp_server_url.endswith("/sse") and not "localhost" in self.mcp_server_url:
            self.mcp_server_url = f"{self.mcp_server_url}/sse"
            
        self.agent: Optional[LlmAgent] = None
        self.toolset: Optional[McpToolset] = None
        self.runner: Optional[Runner] = None
        self.session_service: Optional[InMemorySessionService] = None
        self.app_name = "alphavantage_stock_agent_app"
        self.user_id = "default_user"
        self.session_id = "default_session"
        
        logger.info(f"Initialized AlphaVantageAgentRuntime with MCP Server URL: {self.mcp_server_url}")

    async def initialize_agent(self) -> None:
        """
        Connects to the remote Cloud Run MCP server over SSE, discovers tools,
        and initializes the ADK LlmAgent with these tools.
        """
        logger.info("Configuring McpToolset over SSE Connection...")
        try:
            # SseConnectionParams configures connection parameters for the remote Cloud Run service
            connection_params = SseConnectionParams(
                url=self.mcp_server_url,
                headers={}
            )

            # McpToolset manages the session connection and exposes discovered tools directly
            self.toolset = McpToolset(connection_params=connection_params)

            # Create and configure the LlmAgent
            self.agent = LlmAgent(
                model="gemini-2.5-flash",
                name="AlphaVantageGroundedAgent",
                instruction=(
                    "You are a sophisticated, real-time financial analyst and stock agent. "
                    "You have direct access to the Alpha Vantage tool suite to query current pricing metrics. "
                    "Always use the 'get_stock_quote' tool to verify real-time data before answering user queries. "
                    "Provide precise, professional, and clear summaries of stock performances."
                ),
                tools=[self.toolset]
            )
            
            # Setup ADK 2.0 Session Service and Runner
            logger.info("Initializing ADK Session Service and execution Runner...")
            self.session_service = InMemorySessionService()
            self.runner = Runner(
                agent=self.agent,
                app_name=self.app_name,
                session_service=self.session_service
            )
            
            # Initialize a conversational session (Awaited async coroutine in ADK 2.0)
            await self.session_service.create_session(
                app_name=self.app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            logger.info("ADK LlmAgent & Runner created successfully and session initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize cognitive agent: {e}")
            raise

    async def run_chat(self, prompt: str) -> str:
        """
        Runs a chat query against the initialized ADK agent.
        """
        if not self.runner:
            raise RuntimeError("Agent/Runner has not been initialized. Please call initialize_agent() first.")
        
        logger.info(f"Sending prompt to ADK Agent via Runner: '{prompt}'")
        try:
            # Package the user prompt into types.Content structure
            new_message = types.Content(
                role="user",
                parts=[types.Part(text=prompt)]
            )
            
            final_response = ""
            # Execute agent session and iterate over streamed lifecycle events
            async for event in self.runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=new_message
            ):
                # Capture the final aggregated text response event
                if event.is_final_response() and event.content:
                    final_response = event.content.parts[0].text
                    
            if not final_response:
                raise RuntimeError("Grounded agent did not return a final response payload.")
                
            return final_response
        except Exception as e:
            logger.error(f"Error during agent runner execution: {e}")
            raise

    async def close(self) -> None:
        """
        Safely disposes the MCP server connection context.
        """
        if self.toolset:
            logger.info("Closing McpToolset connection...")
            try:
                await self.toolset.close()
                logger.info("McpToolset connection successfully closed.")
            except Exception as e:
                logger.warning(f"Error during toolset shutdown: {e}")
            self.toolset = None
            self.agent = None
            self.runner = None
            self.session_service = None
stream = None
