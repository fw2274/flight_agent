Multi-Agent Voice-Activated Flight Search System
Project Overview
This project implements a multi-agent system that enables users to search for flights using voice commands. The application is designed to improve accessibility for users who have difficulties with writing or interacting with keypads, including individuals with motor impairments, visual disabilities, or those who prefer voice interaction.

System Architecture
The system consists of three specialized agents working together in a pipeline:

Agent 1: Voice Recognition Agent
The first agent captures spoken input from users and converts it into text. This agent implements speech-to-text technology that processes audio input and produces accurate transcriptions of flight search requests.

Agent 2: Information Extraction Agent
The second agent processes the transcribed text and extracts the essential parameters needed for a flight search. Using natural language processing techniques, this agent identifies and structures key information from conversational speech.

The agent extracts:

Origin and destination cities/airports
Departure and return dates
Number of passengers
Cabin class preferences
Special requirements or preferences
This agent handles different ways users might express their travel needs and normalizes them into structured data that can be used for searching flights.

Agent 3: Flight Search Agent
The third agent executes the flight search based on the structured information from Agent 2. This agent serves as a wrapper around an external flight search tool, handling the technical details of API communication, request formatting, and response processing. It ensures search results are returned in a consistent, user-friendly format.


# Flight Agent (Google ADK + Amadeus + Voice Input)

Small two-step workflow with optional voice input: Gemini interprets a natural-language request (via text or voice) into flight params, then calls the LangGraph `search_flights` tool (Amadeus) to fetch real options.

**NEW:** 🎤 Voice-to-text integration using MCP (Model Context Protocol) - speak your flight requirements instead of typing!

The Amadeus tooling comes from `langgraph_travel_agent` (pulled from https://github.com/fw2274/flight_agent and vendored under `langgraph_travel_agent/backend`). We wrap its `agent_graph.py` primitives so Google ADK can call them directly:
- `agent_graph_module.search_flights` → exposed to ADK via the async `search_flights` wrapper in `flight_search.py` / `flight_search_dual.py`
- `agent_graph_module.amadeus` client → validated on startup to ensure credentials are present

## Quick start

### Text Input Mode
- Prereqs: Python 3.10+, virtualenv, Amadeus credentials, Google API key.
- Setup:
  ```bash
  python -m venv .venv && source .venv/bin/activate
  pip install -r requirements.txt  # or your existing env
  echo "GOOGLE_API_KEY=..." >> .env
  echo "AMADEUS_API_KEY=..." >> .env
  echo "AMADEUS_API_SECRET=..." >> .env
  ```
- Run:
  ```bash
  python flight_search.py --query "Find a round-trip flight from ATL to JFK on Dec 02 returning Dec 15 for 2 adults in economy"
  ```
  Flags: `--verbose` (stream tool calls), `--debug` (full timeline).

### Voice Input Mode 🎤
- Additional prereqs: Rust, microphone
- Setup:
  ```bash
  # 1. Install Rust (if not already)
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

  # 2. Build voice-to-text MCP server
  cd voice-to-text-mcp
  cargo build --release
  ./scripts/download-models.sh  # Choose ggml-base.en.bin
  cd ..

  # 3. Verify setup
  ./test_voice_setup.sh
  ```
- Run:
  ```bash
  # Speak your flight requirement
  python3 flight_search_vtt.py --voice

  # Voice with custom timeout (45 seconds)
  python3 flight_search_vtt.py --voice --voice-timeout 45000
  ```

📖 **See [VOICE_SETUP.md](VOICE_SETUP.md) for detailed voice integration guide**

## What happens
1) Env loads (`.env`), Amadeus client is validated.  
2) A Gemini agent is created with the LangGraph `search_flights` tool.  
3) Your query is analyzed; the tool is called with clean params (IATA codes, ISO dates, class, pax).  
4) Results are returned and printed in a human-friendly format (airline, price, depart/arrive, duration).

## Files you'll care about
- `flight_search.py` — main entry; wires Gemini to the LangGraph tool (text input only)
- `flight_search_vtt.py` — **NEW** flight search with voice-to-text integration (text or voice input)
- `voice_mcp_client.py` — **NEW** Python client for voice-to-text MCP server
- `langgraph_travel_agent/backend/agent_graph.py` — houses the `search_flights` LangChain tool and Amadeus plumbing (sourced from https://github.com/fw2274/flight_agent)
- `flight_search_dual.py` — optional interpreter/executor split (two-agent flow)
- `voice-to-text-mcp/` — **NEW** Rust-based MCP server for speech recognition (cloned from https://github.com/acazau/voice-to-text-mcp)

## Tips
- Dates must be `YYYY-MM-DD`; the agent normalizes common phrases but keep inputs explicit.
- Travel class strings: `ECONOMY`, `PREMIUM_ECONOMY`, `BUSINESS`, `FIRST`.
- For round trips, provide `returnDate`; otherwise it’s treated as one-way.
- Use IATA codes when possible (e.g., `ATL` → `JFK`) to avoid ambiguity.

## Troubleshooting
- Missing keys? Ensure `.env` has `GOOGLE_API_KEY`, `AMADEUS_API_KEY`, `AMADEUS_API_SECRET`.
- Amadeus client missing? Check the prints on startup; credentials must be valid.
- No results? Verify dates are in the future and origin/destination are valid IATA codes.
