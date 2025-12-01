"""
Flight Search with Amadeus API Integration

This script imports the search_flights function from langgraph_travel_agent
and integrates it with Google ADK's Gemini agent.

To run:
1. Ensure GOOGLE_API_KEY, AMADEUS_API_KEY, AMADEUS_API_SECRET are in .env
2. Activate virtual environment: source .venv/bin/activate
3. Run: python flight_search.py [--verbose] [--debug] [--query "your query"]
"""

import os
import sys
import argparse
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

# Load environment variables from root .env FIRST
load_dotenv()

# Add external repo to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'langgraph_travel_agent', 'backend'))

# Import from external repository
import langgraph_travel_agent.backend.agent_graph as agent_graph_module


# Create a plain async function wrapper that Google ADK can call
async def search_flights(
    originLocationCode: str,
    destinationLocationCode: str,
    departureDate: str,
    returnDate: str = None,
    adults: int = 1,
    travelClass: str = "ECONOMY"
):
    """
    Search for flight offers using Amadeus API.

    Args:
        originLocationCode: Origin city name or IATA airport code (e.g., "Atlanta", "ATL")
        destinationLocationCode: Destination city name or IATA airport code
        departureDate: Departure date in YYYY-MM-DD format
        returnDate: Return date for round-trip flights (YYYY-MM-DD), optional
        adults: Number of adult passengers (default: 1)
        travelClass: Cabin class - ECONOMY, PREMIUM_ECONOMY, BUSINESS, or FIRST (default: ECONOMY)

    Returns:
        List of flight options with airline, price, departure/arrival times, and duration
    """
    print(f"→ Flight search: {originLocationCode} → {destinationLocationCode}")
    print(f"   Departure: {departureDate}, Return: {returnDate}, Adults: {adults}, Class: {travelClass}")

    # Get the LangChain tool from the external module
    langchain_tool = agent_graph_module.search_flights

    # Call it via ainvoke (LangChain's async invocation method)
    results = await langchain_tool.ainvoke({
        "originLocationCode": originLocationCode,
        "destinationLocationCode": destinationLocationCode,
        "departureDate": departureDate,
        "returnDate": returnDate,
        "adults": adults,
        "travelClass": travelClass,
        "currencyCode": "USD"
    })

    print(f"✓ Received {len(results) if results else 0} flight results")

    # Convert Pydantic models to dict for JSON serialization
    if results:
        return [r.model_dump() if hasattr(r, 'model_dump') else r for r in results]
    return []


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Flight Search Agent - Powered by Amadeus API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python flight_search.py
  python flight_search.py --verbose
  python flight_search.py --debug
  python flight_search.py --query "Find flights from LAX to NYC"
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
    """Main function to run the flight search agent"""

    # Check required API keys
    google_key = os.getenv("GOOGLE_API_KEY")
    amadeus_key = os.getenv("AMADEUS_API_KEY")
    amadeus_secret = os.getenv("AMADEUS_API_SECRET")

    if not google_key:
        print("⚠️  ERROR: GOOGLE_API_KEY not set in .env file!")
        print("   Get your API key from: https://aistudio.google.com/app/api-keys")
        return

    if not amadeus_key or not amadeus_secret:
        print("⚠️  ERROR: Amadeus API credentials not set in .env file!")
        print("   Get credentials from: https://developers.amadeus.com/register")
        return

    print("✅ All API keys found")

    # Configure retry options
    retry_config = types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504]
    )

    print("🔧 Setting up Amadeus flight search...")

    # Import the amadeus client from the external module to verify it's initialized
    if not hasattr(agent_graph_module, 'amadeus') or agent_graph_module.amadeus is None:
        print("❌ Amadeus client not initialized properly!")
        print("   Check that AMADEUS_API_KEY and AMADEUS_API_SECRET are set in .env")
        return

    print("✅ Amadeus client ready")

    print("🤖 Creating AI agent with flight search capabilities...")

    # Use the search_flights function directly from the external module
    # It's already a LangChain @tool decorated function
    agent = Agent(
        name="flight_assistant",
        model=Gemini(
            model="gemini-2.5-flash-lite",
            retry_options=retry_config
        ),
        description="A travel assistant that can search for flights using Amadeus API",
        instruction="""You are a helpful travel assistant with access to real-time flight data via Amadeus API.

## Your Capabilities
You can help users:
- Search for flights between cities
- Find the cheapest flights
- Look for specific cabin classes
- Handle round-trip and one-way flights

## CRITICAL: How to Present Flight Results

After receiving flight search results, you MUST present them in a clear, formatted way:

**For each flight, display:**
- ✈️ Airline name
- 💰 Total price (with currency)
- 🛫 Departure time (formatted as readable date/time)
- 🛬 Arrival time (formatted as readable date/time)
- ⏱️ Flight duration (if available)

**Example presentation:**
"I found 3 flights for you:

**Flight 1:**
- ✈️ Airline: Delta Air Lines
- 💰 Price: $450.00 USD
- 🛫 Departure: Dec 2, 2024 at 8:00 AM
- 🛬 Arrival: Dec 2, 2024 at 11:30 AM
- ⏱️ Duration: PT3H30M

**Flight 2:**
..."

Always format times in a human-readable way and sort by price (cheapest first).

## CRITICAL: How to Call search_flights Tool

When users ask about flights, you MUST call the search_flights tool with these EXACT parameter names:

### Required Parameters:
- originLocationCode: IATA airport code (e.g., "ATL", "LAX", "ORD")
  → Use 3-letter IATA codes, NOT city names
- destinationLocationCode: IATA airport code (e.g., "JFK", "LAX", "NRT")
  → Use 3-letter IATA codes, NOT city names
- departureDate: Departure date in YYYY-MM-DD format
  → Convert all dates to this format

### Optional Parameters:
- returnDate: Return date in YYYY-MM-DD format (REQUIRED for round-trip flights)
- adults: Number of adult passengers (integer, default: 1)
- travelClass: Travel class - MUST be exactly one of these strings: "ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"
  → For economy class, use the string "ECONOMY" (not "M" or any other code)

### Example Tool Calls:

Round-Trip Flight:
User: "Find a round-trip flight from ATL to JFK on Dec 02, returning Dec 15, 2 adults, economy"
Tool Call:
{
  "originLocationCode": "Atlanta",
  "destinationLocationCode": "New York",
  "departureDate": "2024-12-02",
  "returnDate": "2024-12-15",
  "adults": 2,
  "travelClass": "ECONOMY"
}

One-Way Flight:
User: "One-way flight from Los Angeles to Tokyo on January 10"
Tool Call:
{
  "originLocationCode": "Los Angeles",
  "destinationLocationCode": "Tokyo",
  "departureDate": "2025-01-10"
}

## Date Parsing Rules:
- "Dec 02" → "2024-12-02" (assume current year 2024)
- "January 10" → "2025-01-10"
- Always output dates in YYYY-MM-DD format

## City to IATA Code Mapping:
- Atlanta → "ATL"
- New York/NYC → "JFK" (or "LGA", "EWR")
- Los Angeles/LA → "LAX"
- Chicago → "ORD" (or "MDW")
- **IMPORTANT**: Always use IATA airport codes, not city names

Always be helpful, clear, and provide detailed information about flight options.""",
        tools=[search_flights],  # Use the LangChain tool directly
    )

    # Create runner
    runner = InMemoryRunner(agent=agent)

    print("✨ Flight Assistant Ready!\n")
    print("=" * 60)

    # Determine query
    if args.query:
        query = args.query
    else:
        query = "Find a round-trip flight from ATL to JFK in Dec 02 and return on Dec 15 for 2 adults in economy class"

    print(f"🔍 Query: {query}\n")
    print("⏳ Searching for flights...\n")

    # Run with comprehensive error handling
    try:
        events = await runner.run_debug(query, verbose=args.verbose)

        # Inspect for tool errors
        tool_errors = []
        for event in events:
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

        # Display errors if found
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

        # Extract and display the agent's final response
        final_response = None
        for event in reversed(events):  # Check from last event backwards
            if event.author == "flight_assistant" and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_response = part.text
                        break
                if final_response:
                    break

        if final_response:
            print("\n" + "=" * 60)
            print("📋 FLIGHT SEARCH RESULTS")
            print("=" * 60 + "\n")
            print(final_response)
            print()

        # Debug output if requested
        if args.debug:
            print("\n" + "=" * 60)
            print("🔍 DEBUG: Event Timeline")
            print("=" * 60)

            for i, event in enumerate(events, 1):
                print(f"\n[Event {i}]")
                print(f"  Author: {event.author}")
                print(f"  ID: {event.id}")
                print(f"  Timestamp: {event.timestamp}")

                if calls := event.get_function_calls():
                    for call in calls:
                        print(f"\n  📞 Tool Call: {call.name}")
                        print(f"     Call ID: {call.id}")
                        print(f"     Arguments: {call.args}")

                if responses := event.get_function_responses():
                    for resp in responses:
                        print(f"\n  📨 Tool Response:")
                        print(f"     Response ID: {resp.id}")
                        response_preview = str(resp.response)[:500]
                        if len(str(resp.response)) > 500:
                            response_preview += "..."
                        print(f"     Data: {response_preview}")

                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            text_preview = part.text[:300]
                            if len(part.text) > 300:
                                text_preview += "..."
                            print(f"\n  💬 Text: {text_preview}")

                if event.actions.state_delta:
                    print(f"\n  🔄 State Changes: {event.actions.state_delta}")

        print("\n" + "=" * 60)
        print("✅ Search complete!")
        print("=" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ EXECUTION ERROR")
        print("=" * 60)
        print(f"\nError Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        if args.debug:
            print("\n🔍 Stack trace:")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🛫 Flight Search Agent - Powered by Amadeus API")
    print("=" * 60 + "\n")

    args = parse_arguments()
    asyncio.run(main(args))
