import asyncio
import subprocess
import json
import os
import sys
import requests

# Ensure python path is configured to import from the src/ directory
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.agent_runtime.agent import AlphaVantageAgentRuntime

def get_terraform_outputs() -> dict:
    """
    Query the local Terraform state to dynamically resolve all service URLs.
    """
    print(" Resolving live service URLs from Terraform outputs...")
    try:
        result = subprocess.run(
            ["terraform", "output", "-json"],
            cwd="terraform/app",
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except Exception as e:
        print(f" Failed to read live Terraform outputs: {e}")
        return {}

async def run_local_adk_test(mcp_url: str):
    """
    Instantiates the Vertex AI ADK agent runtime locally on your machine
    and connects to the remote Cloud Run MCP server.
    """
    print("\n" + "="*50)
    print(" METHOD 1: TESTING LOCAL VERTEX AI ADK CLIENT")
    print("="*50)
    print(" Instantiating AlphaVantageAgentRuntime client locally...")
    runtime = AlphaVantageAgentRuntime(mcp_server_url=mcp_url)
    
    try:
        print(" Handshaking and loading MCP tools dynamically...")
        await runtime.initialize_agent()
        
        prompt = "What is the current trading price of Apple (AAPL) stock?"
        print(f" Sending prompt to local ADK Agent: '{prompt}'")
        
        response = await runtime.run_chat(prompt)
        print("\n=== Local ADK Agent Response ===")
        print(response)
    except Exception as e:
        print(f" Error during local ADK test: {e}")
    finally:
        await runtime.close()

def run_cloud_service_test(agent_url: str):
    """
    Sends a REST POST request to hit the live, cloud-deployed
    Starlette Cognitive Agent Runtime on Google Cloud Run.
    """
    print("\n" + "="*50)
    print(" METHOD 2: TESTING LIVE CLOUD-DEPLOYED COGNITIVE AGENT")
    print("="*50)
    chat_url = f"{agent_url.rstrip('/')}/chat"
    print(f" Target Cloud Run Endpoint: POST {chat_url}")
    
    prompt = "What is the daily percentage change of Microsoft (MSFT) stock?"
    payload = {"prompt": prompt}
    headers = {"Content-Type": "application/json"}
    
    print(f" Sending prompt to Cloud Service: '{prompt}'")
    try:
        response = requests.post(chat_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print("\n=== Live Cloud Run Agent Response ===")
        print(data.get("response", "No response field returned."))
    except Exception as e:
        print(f" Error during Cloud Run service test: {e}")

async def main():
    outputs = get_terraform_outputs()
    
    mcp_url = outputs.get("mcp_service_url", {}).get("value")
    agent_url = outputs.get("agent_service_url", {}).get("value")
    
    # Check if we have the live deployed Cognitive Cloud Run service
    if agent_url:
        run_cloud_service_test(agent_url)
    else:
        print("\n No 'agent_service_url' found in Terraform. Skipping live Cloud Run service test.")
        
    # Check if we can fall back or run the local client test
    if mcp_url:
        await run_local_adk_test(mcp_url)
    else:
        print("\n No 'mcp_service_url' found in Terraform. Make sure the backend is deployed.")

if __name__ == "__main__":
    # Check for active GCP credentials
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") and not os.path.exists(os.path.expanduser("~/.config/gcloud/application_default_credentials.json")):
        print(" WARNING: No GCP credentials found. Please run: gcloud auth application-default login")
    
    asyncio.run(main())
