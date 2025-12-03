"""
Simplified Flight Search for ARM Tablet
This version has reduced dependencies and is optimized for Android/Termux

Usage:
  python flight_search_tablet.py --query "Find flights from LAX to NYC"
  python flight_search_tablet.py --voice  # Requires Termux microphone permissions
"""

import os
import sys
import argparse
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simplified imports that work in Termux
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not available")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available")


class SimplifiedFlightSearch:
    """Simplified flight search that works on ARM tablets"""

    def __init__(self, google_api_key: str, amadeus_key: str, amadeus_secret: str):
        self.google_api_key = google_api_key
        self.amadeus_key = amadeus_key
        self.amadeus_secret = amadeus_secret
        self.amadeus_token = None

        if GEMINI_AVAILABLE:
            genai.configure(api_key=google_api_key)
            self.model = genai.GenerativeModel('gemini-pro')

    def get_amadeus_token(self) -> str:
        """Get Amadeus API access token"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests library not available")

        url = "https://api.amadeus.com/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.amadeus_key,
            "client_secret": self.amadeus_secret
        }

        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()["access_token"]

    def parse_query(self, query: str) -> Dict[str, Any]:
        """Use Gemini to parse natural language query into structured params"""
        if not GEMINI_AVAILABLE:
            # Fallback to simple parsing
            return self._simple_parse(query)

        prompt = f"""Parse this flight search query into JSON format.
Return ONLY valid JSON with these fields:
{{
  "originLocationCode": "<IATA code>",
  "destinationLocationCode": "<IATA code>",
  "departureDate": "YYYY-MM-DD",
  "returnDate": "YYYY-MM-DD or null",
  "adults": <integer>,
  "travelClass": "ECONOMY|PREMIUM_ECONOMY|BUSINESS|FIRST"
}}

Query: {query}

Rules:
- Use 3-letter IATA airport codes
- Dates must be YYYY-MM-DD format
- Default adults to 1
- Default travelClass to ECONOMY
- If one-way, set returnDate to null
"""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()

            # Remove markdown code blocks if present
            if text.startswith("```"):
                text = text.strip("`").replace("json", "", 1).strip()

            params = json.loads(text)
            return params
        except Exception as e:
            print(f"Warning: Gemini parsing failed: {e}")
            print("Falling back to simple parsing...")
            return self._simple_parse(query)

    def _simple_parse(self, query: str) -> Dict[str, Any]:
        """Simple fallback parser without AI"""
        # Very basic parsing - just for demo
        words = query.upper().split()

        # Look for airport codes (3 uppercase letters)
        codes = [w for w in words if len(w) == 3 and w.isalpha()]

        return {
            "originLocationCode": codes[0] if len(codes) > 0 else "LAX",
            "destinationLocationCode": codes[1] if len(codes) > 1 else "JFK",
            "departureDate": "2025-12-15",  # Default date
            "returnDate": "2025-12-22",
            "adults": 1,
            "travelClass": "ECONOMY"
        }

    def search_flights(self, params: Dict[str, Any]) -> list:
        """Search for flights using Amadeus API"""
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("requests library not available")

        # Get access token
        if not self.amadeus_token:
            self.amadeus_token = self.get_amadeus_token()

        url = "https://api.amadeus.com/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {self.amadeus_token}"}

        query_params = {
            "originLocationCode": params["originLocationCode"],
            "destinationLocationCode": params["destinationLocationCode"],
            "departureDate": params["departureDate"],
            "adults": params.get("adults", 1),
            "travelClass": params.get("travelClass", "ECONOMY"),
            "currencyCode": "USD",
            "max": 5
        }

        if params.get("returnDate"):
            query_params["returnDate"] = params["returnDate"]

        try:
            response = requests.get(url, headers=headers, params=query_params)
            response.raise_for_status()
            data = response.json()

            return self._format_results(data.get("data", []))
        except requests.exceptions.HTTPError as e:
            print(f"API Error: {e}")
            if e.response:
                print(f"Response: {e.response.text}")
            return []

    def _format_results(self, flights: list) -> list:
        """Format flight results for display"""
        results = []

        for idx, flight in enumerate(flights[:5], 1):
            try:
                price = flight.get("price", {}).get("total", "N/A")
                currency = flight.get("price", {}).get("currency", "USD")

                itineraries = flight.get("itineraries", [])
                if not itineraries:
                    continue

                # Get first segment details
                first_itinerary = itineraries[0]
                segments = first_itinerary.get("segments", [])
                if not segments:
                    continue

                first_segment = segments[0]
                departure = first_segment.get("departure", {})
                arrival = first_segment.get("arrival", {})

                duration = first_itinerary.get("duration", "Unknown")

                result = {
                    "number": idx,
                    "price": f"{price} {currency}",
                    "departure": {
                        "airport": departure.get("iataCode", "Unknown"),
                        "time": departure.get("at", "Unknown")
                    },
                    "arrival": {
                        "airport": arrival.get("iataCode", "Unknown"),
                        "time": arrival.get("at", "Unknown")
                    },
                    "duration": duration,
                    "carrier": first_segment.get("carrierCode", "Unknown")
                }

                results.append(result)
            except Exception as e:
                print(f"Warning: Error formatting flight {idx}: {e}")
                continue

        return results

    def display_results(self, results: list):
        """Display flight results"""
        if not results:
            print("\nNo flights found. Try different dates or airports.")
            return

        print("\n" + "=" * 60)
        print("FLIGHT SEARCH RESULTS")
        print("=" * 60)

        for flight in results:
            print(f"\nFlight #{flight['number']}")
            print(f"  Price: {flight['price']}")
            print(f"  Carrier: {flight['carrier']}")
            print(f"  Departure: {flight['departure']['airport']} at {flight['departure']['time']}")
            print(f"  Arrival: {flight['arrival']['airport']} at {flight['arrival']['time']}")
            print(f"  Duration: {flight['duration']}")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Simplified Flight Search for ARM Tablets")
    parser.add_argument("--query", type=str, help="Flight search query")
    parser.add_argument("--voice", action="store_true", help="Use voice input (experimental)")
    args = parser.parse_args()

    # Check API keys
    google_key = os.getenv("GOOGLE_API_KEY")
    amadeus_key = os.getenv("AMADEUS_API_KEY")
    amadeus_secret = os.getenv("AMADEUS_API_SECRET")

    if not google_key:
        print("Error: GOOGLE_API_KEY not set in .env file")
        return 1

    if not amadeus_key or not amadeus_secret:
        print("Error: Amadeus API credentials not set in .env file")
        return 1

    # Initialize search
    search = SimplifiedFlightSearch(google_key, amadeus_key, amadeus_secret)

    # Get query
    if args.query:
        query = args.query
    elif args.voice:
        print("Voice input not yet implemented for tablet version")
        print("Please use --query instead")
        return 1
    else:
        # Interactive mode
        print("Enter your flight search query:")
        print("Example: Find flights from LAX to NYC on December 15")
        query = input("> ")

    print(f"\nProcessing query: {query}")
    print("-" * 60)

    # Parse query
    print("\nParsing flight requirements...")
    params = search.parse_query(query)
    print("Extracted parameters:")
    print(json.dumps(params, indent=2))

    # Search flights
    print("\nSearching for flights...")
    results = search.search_flights(params)

    # Display results
    search.display_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
