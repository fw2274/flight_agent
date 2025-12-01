"""
Dual-agent flight search using Google ADK.

Flow:
1) Interpreter agent (LLM-only) turns natural language into clean parameters.
2) Executor agent calls the LangGraph `search_flights` tool with those params.

To run:
  python flight_search_dual.py [--verbose] [--debug] [--query "..."]
"""

import os
import sys
import argparse
import asyncio
import json
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.genai import types

# Load environment variables from root .env
load_dotenv()

# Add external repo to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "langgraph_travel_agent", "backend"))
import langgraph_travel_agent.backend.agent_graph as agent_graph_module  # noqa: E402


# Wrapper around LangGraph search_flights tool so Google ADK can call it
async def search_flights(
    originLocationCode: str,
    destinationLocationCode: str,
    departureDate: str,
    returnDate: Optional[str] = None,
    adults: int = 1,
    travelClass: str = "ECONOMY",
):
    print(f"→ Flight search: {originLocationCode} → {destinationLocationCode}")
    print(f"   Departure: {departureDate}, Return: {returnDate}, Adults: {adults}, Class: {travelClass}")

    langchain_tool = agent_graph_module.search_flights
    results = await langchain_tool.ainvoke(
        {
            "originLocationCode": originLocationCode,
            "destinationLocationCode": destinationLocationCode,
            "departureDate": departureDate,
            "returnDate": returnDate,
            "adults": adults,
            "travelClass": travelClass,
            "currencyCode": "USD",
        }
    )

    print(f"✓ Received {len(results) if results else 0} flight results")
    if results:
        return [r.model_dump() if hasattr(r, "model_dump") else r for r in results]
    return []


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Dual-agent Flight Search (Interpreter + Executor)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python flight_search_dual.py
  python flight_search_dual.py --verbose
  python flight_search_dual.py --debug
  python flight_search_dual.py --query "Find flights from LAX to NYC"
        """,
    )
    parser.add_argument("--debug", action="store_true", help="Print event timeline")
    parser.add_argument("--verbose", action="store_true", help="Show tool calls/responses in real-time")
    parser.add_argument("--query", type=str, help="Flight search query (overrides default)")
    return parser.parse_args()


def build_retry_config():
    return types.HttpRetryOptions(attempts=5, exp_base=7, initial_delay=1, http_status_codes=[429, 500, 503, 504])


def build_interpreter_agent():
    """
    LLM-only agent that converts NL request into structured params.
    """
    return Agent(
        name="interpreter_agent",
        model=Gemini(model="gemini-2.5-flash-lite"),
        description="Parses natural language into flight search parameters",
        instruction="""You are a travel request interpreter. Convert the user's message into strict JSON.

Return ONLY a JSON object with these fields (no prose):
{
  "originLocationCode": "<IATA code>",
  "destinationLocationCode": "<IATA code>",
  "departureDate": "YYYY-MM-DD",
  "returnDate": "YYYY-MM-DD or null",
  "adults": <int default 1>,
  "travelClass": "ECONOMY|PREMIUM_ECONOMY|BUSINESS|FIRST"
}

Rules:
- Prefer 3-letter IATA codes; infer if user gave city names.
- If return date not provided, set null.
- Default travelClass to ECONOMY.
- Default adults to 1 if not specified.
- Dates must be absolute YYYY-MM-DD; resolve relative dates to the next occurrence.
- Do not ask questions; make best-effort assumptions.
""",
    )


def build_executor_agent():
    """
    Tool-using agent that takes clean params and calls search_flights.
    """
    return Agent(
        name="executor_agent",
        model=Gemini(model="gemini-2.5-flash-lite"),
        description="Executes flight searches with provided parameters",
        instruction="""You are a precise executor. Given validated parameters, call the tool without re-interpreting.

Process:
- Use the provided parameters verbatim.
- Call search_flights exactly once.
- After the tool returns, present flights sorted by price if available.
- Keep the response concise and formatted for readability.
""",
        tools=[search_flights],
    )


async def run_agent(agent: Agent, message: str, verbose: bool) -> list:
    runner = InMemoryRunner(agent=agent)
    return await runner.run_debug(message, verbose=verbose)


def extract_final_text(events) -> Optional[str]:
    for event in reversed(events):
        if event.author and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    return part.text
    return None


def parse_interpreter_output(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()
    try:
        data = json.loads(cleaned)
        required = ["originLocationCode", "destinationLocationCode", "departureDate"]
        for key in required:
            if not data.get(key):
                raise ValueError(f"Missing required field: {key}")
        data.setdefault("returnDate", None)
        data.setdefault("adults", 1)
        data.setdefault("travelClass", "ECONOMY")
        return data
    except Exception as exc:
        raise ValueError(f"Failed to parse interpreter output: {exc}\nRaw: {text}") from exc


async def run_interpreter(query: str, verbose: bool):
    interpreter = build_interpreter_agent()
    events = await run_agent(interpreter, query, verbose)
    text = extract_final_text(events)
    if not text:
        raise ValueError("Interpreter returned no text")
    params = parse_interpreter_output(text)
    return params, events


async def run_executor(params: Dict[str, Any], verbose: bool):
    executor = build_executor_agent()
    prompt = (
        "Use the provided parameters and call search_flights. "
        "Do not change them.\n"
        f"Parameters:\n{json.dumps(params, indent=2)}"
    )
    events = await run_agent(executor, prompt, verbose)
    return events


def print_tool_errors(events):
    tool_errors = []
    for event in events:
        if responses := event.get_function_responses():
            for resp in responses:
                resp_str = str(resp.response)
                if "error" in resp_str.lower() or "failed" in resp_str.lower():
                    tool_errors.append({"tool_id": resp.id, "response": resp.response, "timestamp": event.timestamp})
    if tool_errors:
        print("\n" + "=" * 60)
        print("⚠️  TOOL EXECUTION ERRORS DETECTED")
        print("=" * 60)
        for error in tool_errors:
            print(f"\n   Tool ID: {error['tool_id']}")
            print(f"   Error Response:")
            print(f"   {error['response']}")
        print()


def print_debug(events):
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
                response_preview = str(resp.response)[:300]
                if len(str(resp.response)) > 300:
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


async def main(args):
    google_key = os.getenv("GOOGLE_API_KEY")
    amadeus_key = os.getenv("AMADEUS_API_KEY")
    amadeus_secret = os.getenv("AMADEUS_API_SECRET")

    if not google_key:
        print("⚠️  ERROR: GOOGLE_API_KEY not set in .env file!")
        return
    if not amadeus_key or not amadeus_secret:
        print("⚠️  ERROR: Amadeus API credentials not set in .env file!")
        return

    if not hasattr(agent_graph_module, "amadeus") or agent_graph_module.amadeus is None:
        print("❌ Amadeus client not initialized properly!")
        return

    query = args.query or "Find a round-trip flight from ATL to JFK on Dec 02 returning Dec 15 for 2 adults in economy"

    print("\n" + "=" * 60)
    print("🧭 Interpreter Agent")
    print("=" * 60 + "\n")
    try:
        params, interp_events = await run_interpreter(query, args.verbose)
        print("✓ Interpreter output:")
        print(json.dumps(params, indent=2))
    except Exception as e:
        print(f"❌ Interpreter failed: {e}")
        return

    print("\n" + "=" * 60)
    print("🛠️  Executor Agent")
    print("=" * 60 + "\n")
    try:
        exec_events = await run_executor(params, args.verbose)
        print_tool_errors(exec_events)
        final_response = extract_final_text(exec_events)
        if final_response:
            print("\n" + "=" * 60)
            print("📋 FLIGHT SEARCH RESULTS")
            print("=" * 60 + "\n")
            print(final_response)
            print()
    except Exception as e:
        print(f"❌ Executor failed: {e}")
        return

    if args.debug:
        print_debug(interp_events)
        print_debug(exec_events)

    print("\n" + "=" * 60)
    print("✅ Dual-agent search complete!")
    print("=" * 60)


if __name__ == "__main__":
    args = parse_arguments()
    asyncio.run(main(args))
