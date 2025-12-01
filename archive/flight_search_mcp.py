"""
Flight Search MCP Server Integration Example

This script demonstrates how to use the Flight Search MCP server
from https://flights.fctolabs.com/ with Google ADK in VS Code.

To run this script:
1. Make sure you have GOOGLE_API_KEY environment variable set
2. Activate your virtual environment: source .venv/bin/activate
3. Run: python flight_search_mcp.py [--verbose] [--debug] [--query "your query"]
"""

import os
import sys
import argparse
import asyncio
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool import McpToolset
from google.genai import types
from mcp import StdioServerParameters


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Flight Search Agent - Powered by MCP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python flight_search_mcp.py
  python flight_search_mcp.py --verbose
  python flight_search_mcp.py --debug
  python flight_search_mcp.py --query "Find flights from LAX to NYC"
        """
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with detailed error messages and event timeline'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show all tool calls and responses in real-time'
    )
    parser.add_argument(
        '--query',
        type=str,
        help='Flight search query (overrides default query in script)'
    )
    return parser.parse_args()


async def main(args):
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

    # Validate MCP connection (pre-check)
    try:
        print("🔍 Validating MCP connection...")
        tools = await flight_tools.get_tools()
        print(f"✅ MCP connection successful ({len(tools)} tools available)")
        if args.debug:
            print(f"   Available tools: {[t.name for t in tools]}")
    except Exception as e:
        print(f"❌ MCP connection failed: {e}")
        print("   Make sure https://flights.fctolabs.com/mcp is accessible")
        print("   Check network connectivity and npx installation")
        if args.debug:
            import traceback
            traceback.print_exc()
        return

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

## Your Capabilities
You can help users:
- Search for flights between cities
- Find the cheapest flights
- Look for nonstop routes
- Search flight calendars for best prices
- Get information about airports, airlines, and routes
- Provide booking URLs

## CRITICAL: How to Call search_flights Tool

When users ask about flights, you MUST call the search_flights tool with these EXACT parameter names:

### Required Parameters:
- origin: City name or IATA airport code (e.g., "Atlanta", "Los Angeles", "ATL")
  → Prefer FULL CITY NAMES over codes (e.g., "Atlanta" not "ATL")
- destination: City name or IATA airport code
  → Prefer FULL CITY NAMES over codes
- depart_date: Departure date in YYYY-MM-DD format
  → Convert all dates to this format

### Optional Parameters:
- return_date: Return date in YYYY-MM-DD format (REQUIRED for round-trip flights)
- adults: Number of adult passengers (integer, default: 1)
- cabin_class: Travel class - MUST be exactly one of these strings: "economy", "premium_economy", "business", "first"
  → For economy class, use the string "economy" (not "M" or any other code)

### Example Tool Calls:

Round-Trip Flight:
User: "Find a round-trip flight from ATL to JFK on Dec 02, returning Dec 15, 2 adults, economy"
Tool Call:
{
  "origin": "Atlanta",
  "destination": "New York",
  "depart_date": "2024-12-02",
  "return_date": "2024-12-15",
  "adults": 2,
  "cabin_class": "economy"
}

One-Way Flight:
User: "One-way flight from Los Angeles to Tokyo on January 10"
Tool Call:
{
  "origin": "Los Angeles",
  "destination": "Tokyo",
  "depart_date": "2025-01-10"
}

## Date Parsing Rules:
- "Dec 02" → "2024-12-02" (assume current year 2024)
- "January 10" → "2025-01-10"
- Always output dates in YYYY-MM-DD format

## City Name Mapping:
- ATL → "Atlanta"
- JFK/NYC → "New York"
- LAX/LA → "Los Angeles"
- Use city names, not airport codes, when calling the tool

Always be helpful, clear, and provide detailed information about flight options.""",
        tools=[flight_tools],
    )

    # Create a runner
    runner = InMemoryRunner(agent=agent)

    print("✨ Flight Assistant Ready!\n")
    print("=" * 60)

    # Determine which query to use
    if args.query:
        query = args.query
    else:
        # Default query - can be modified for testing
        query = "Find a round-trip flight from ATL to JFK in Dec 02 and return on Dec 15 for 2 adults in economy class"

        # Other example queries:
        # query = "What are the cheapest flights from Los Angeles to London in December?"
        # query = "Find nonstop flights from Chicago to Tokyo"
        # query = "Show me flight prices from Seattle to Paris for the entire month of January"

    print(f"🔍 Query: {query}\n")
    print("⏳ Searching for flights...\n")

    # Run the query with comprehensive error handling
    try:
        events = await runner.run_debug(query, verbose=args.verbose)

        # Inspect events for tool errors
        tool_errors = []
        for event in events:
            # Check function responses for errors
            if responses := event.get_function_responses():
                for resp in responses:
                    resp_str = str(resp.response)
                    if 'error' in resp_str.lower() or 'failed' in resp_str.lower():
                        tool_errors.append({
                            'tool_id': resp.id,
                            'response': resp.response,
                            'timestamp': event.timestamp,
                            'author': event.author
                        })

        # Display tool errors if found
        if tool_errors:
            print("\n" + "=" * 60)
            print("⚠️  TOOL EXECUTION ERRORS DETECTED")
            print("=" * 60)
            for error in tool_errors:
                print(f"\n   Tool ID: {error['tool_id']}")
                print(f"   Author: {error['author']}")
                print(f"   Error Response:")
                print(f"   {error['response']}")
            print()

        # Show detailed debug output if requested
        if args.debug:
            print("\n" + "=" * 60)
            print("🔍 DEBUG: Event Timeline")
            print("=" * 60)

            for i, event in enumerate(events, 1):
                print(f"\n[Event {i}]")
                print(f"  Author: {event.author}")
                print(f"  ID: {event.id}")
                print(f"  Timestamp: {event.timestamp}")

                # Show tool calls
                if calls := event.get_function_calls():
                    for call in calls:
                        print(f"\n  📞 Tool Call: {call.name}")
                        print(f"     Call ID: {call.id}")
                        print(f"     Arguments: {call.args}")

                # Show tool responses
                if responses := event.get_function_responses():
                    for resp in responses:
                        print(f"\n  📨 Tool Response:")
                        print(f"     Response ID: {resp.id}")
                        response_preview = str(resp.response)[:200]
                        if len(str(resp.response)) > 200:
                            response_preview += "..."
                        print(f"     Data: {response_preview}")

                # Show text content
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            text_preview = part.text[:150]
                            if len(part.text) > 150:
                                text_preview += "..."
                            print(f"\n  💬 Text: {text_preview}")

                # Show state changes
                if event.actions.state_delta:
                    print(f"\n  🔄 State Changes: {event.actions.state_delta}")

        print("\n" + "=" * 60)
        print("✅ Search complete!")
        print("=" * 60)

    except ConnectionError as e:
        print("\n" + "=" * 60)
        print("❌ MCP CONNECTION ERROR")
        print("=" * 60)
        print(f"\n{e}")
        print("\n💡 Possible causes:")
        print("   - The MCP server at flights.fctolabs.com may be unreachable")
        print("   - Network connectivity issues")
        print("   - The remote server might be temporarily down")
        if args.debug:
            print("\n🔍 Stack trace:")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ EXECUTION ERROR")
        print("=" * 60)
        print(f"\nError Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        print("\n💡 Try running with --debug flag for more details")
        if args.debug:
            print("\n🔍 Stack trace:")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🛫 Flight Search Agent - Powered by MCP")
    print("=" * 60 + "\n")

    # Parse command line arguments
    args = parse_arguments()

    # Run the main function with arguments
    asyncio.run(main(args))
