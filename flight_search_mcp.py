"""
Flight Search MCP Server Integration Example

This script demonstrates how to use the Flight Search MCP server
from https://flights.fctolabs.com/ with Google ADK in VS Code.

To run this script:
1. Make sure you have GOOGLE_API_KEY environment variable set
2. Activate your virtual environment: source .venv/bin/activate
3. Run: python flight_search_mcp.py
"""

import os
import asyncio
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool import McpToolset
from google.genai import types
from mcp import StdioServerParameters


async def main():
    """
    Main function to run the flight search agent
    """

    # Check if API key is set
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  ERROR: GOOGLE_API_KEY environment variable not set!")
        print("   Get your API key from: https://aistudio.google.com/app/api-keys")
        print("\n   Then set it:")
        print("   export GOOGLE_API_KEY='your-key-here'")
        return

    print("✅ GOOGLE_API_KEY found")

    # Configure retry options for API calls
    retry_config = types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504]
    )

    print("🔧 Setting up Flight Search MCP server...")

    # Create MCP toolset for flight search
    # This connects to the remote MCP server at flights.fctolabs.com
    flight_tools = McpToolset(
        connection_params=StdioServerParameters(
            command="npx",
            args=["mcp-remote", "https://flights.fctolabs.com/mcp"]
        )
    )

    print("🤖 Creating AI agent with flight search capabilities...")

    # Create an agent with flight search tools
    agent = Agent(
        name="flight_assistant",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=retry_config
        ),
        description="A travel assistant that can search for flights and provide booking information",
        instruction="""You are a helpful travel assistant with access to real-time flight data.
        You can help users:
        - Search for flights between cities
        - Find the cheapest flights
        - Look for nonstop routes
        - Search flight calendars for best prices
        - Get information about airports, airlines, and routes
        - Provide booking URLs

        Always be helpful, clear, and provide detailed information about flight options.""",
        tools=[flight_tools],
    )

    # Create a runner
    runner = InMemoryRunner(agent=agent)

    print("✨ Flight Assistant Ready!\n")
    print("=" * 60)

    # Example queries - uncomment to try different ones

    # Query 1: Simple flight search
    query = "Find a one-way flight from SFO to NYC on Jan 7 for 2 adults in economy class"

    # Query 2: Cheapest flights
    # query = "What are the cheapest flights from Los Angeles to London in December?"

    # Query 3: Nonstop flights
    # query = "Find nonstop flights from Chicago to Tokyo"

    # Query 4: Calendar search
    # query = "Show me flight prices from Seattle to Paris for the entire month of January"

    print(f"🔍 Query: {query}\n")
    print("⏳ Searching for flights...\n")

    # Run the query
    response = await runner.run_debug(query)

    print("=" * 60)
    print("\n✅ Search complete!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🛫 Flight Search Agent - Powered by MCP")
    print("=" * 60 + "\n")

    asyncio.run(main())
