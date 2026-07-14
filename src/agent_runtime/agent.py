import asyncio
import logging
from typing import Optional
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams

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
        # Ensure url ends with /sse or similar if the server uses that path
        self.mcp_server_url = mcp_server_url.rstrip("/")
        self.agent: Optional[LlmAgent] = None
        self.exit_stack = None
        logger.info(f"Initialized AlphaVantageAgentRuntime with MCP Server URL: {self.mcp_server_url}")

    async def initialize_agent(self) -> None:
        """
        Connects to the remote Cloud Run MCP server over SSE, discovers tools,
        and initializes the ADK LlmAgent with these tools.
        """
        logger.info("Connecting to MCP SSE Server and discovering tools...")
        try:
            # SseServerParams configures connection parameters for the remote Cloud Run service
            connection_params = SseServerParams(
                url=self.mcp_server_url,
                headers={}
            )

            # MCPToolset handles the handshake and translates MCP tools to ADK-compatible tools
            tools, exit_stack = await MCPToolset.from_server(connection_params=connection_params)
            self.exit_stack = exit_stack
            logger.info(f"Successfully loaded {len(tools)} tools from MCP server.")

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
                tools=tools
            )
            logger.info("ADK LlmAgent created successfully and equipped with MCP tools.")
        except Exception as e:
            logger.error(f"Failed to initialize cognitive agent: {e}")
            if self.exit_stack:
                await self.exit_stack.aclose()
            raise

    async def run_chat(self, prompt: str) -> str:
        """
        Runs a chat query against the initialized ADK agent.
        """
        if not self.agent:
            raise RuntimeError("Agent has not been initialized. Please call initialize_agent() first.")
        
        logger.info(f"Sending prompt to ADK Agent: '{prompt}'")
        try:
            # Execute chat message using ADK Agent interface
            response = await self.agent.chat(prompt)
            return str(response)
        except Exception as e:
            logger.error(f"Error during agent chat invocation: {e}")
            raise

    async def close(self) -> None:
        """
        Safely disposes the MCP server connection context.
        """
        if self.exit_stack:
            logger.info("Closing MCP connection context stack...")
            await self.exit_stack.aclose()
            logger.info("MCP connection successfully closed.")
            self.exit_stack = None
            self.agent = None
