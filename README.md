# Flight Agent (Google ADK + Amadeus)

Small two-step workflow: Gemini interprets a natural-language request into flight params, then calls the LangGraph `search_flights` tool (Amadeus) to fetch real options.

## Quick start
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

## What happens
1) Env loads (`.env`), Amadeus client is validated.  
2) A Gemini agent is created with the LangGraph `search_flights` tool.  
3) Your query is analyzed; the tool is called with clean params (IATA codes, ISO dates, class, pax).  
4) Results are returned and printed in a human-friendly format (airline, price, depart/arrive, duration).

## Files you’ll care about
- `flight_search.py` — main entry; wires Gemini to the LangGraph tool.
- `langgraph_travel_agent/backend/agent_graph.py` — houses the `search_flights` LangChain tool and Amadeus plumbing.
- `flight_search_dual.py` — optional interpreter/executor split (two-agent flow).

## Tips
- Dates must be `YYYY-MM-DD`; the agent normalizes common phrases but keep inputs explicit.
- Travel class strings: `ECONOMY`, `PREMIUM_ECONOMY`, `BUSINESS`, `FIRST`.
- For round trips, provide `returnDate`; otherwise it’s treated as one-way.
- Use IATA codes when possible (e.g., `ATL` → `JFK`) to avoid ambiguity.

## Troubleshooting
- Missing keys? Ensure `.env` has `GOOGLE_API_KEY`, `AMADEUS_API_KEY`, `AMADEUS_API_SECRET`.
- Amadeus client missing? Check the prints on startup; credentials must be valid.
- No results? Verify dates are in the future and origin/destination are valid IATA codes.
