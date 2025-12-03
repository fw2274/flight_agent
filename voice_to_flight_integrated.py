"""
Integrated Voice-to-Flight Search for ARM Tablets
Full pipeline: Voice Input → Whisper Transcription → Gemini Parsing → Amadeus Flight Search

Usage:
  # Voice mode (default)
  python voice_to_flight_integrated.py

  # Text mode (bypass voice)
  python voice_to_flight_integrated.py --text "Find flights from LAX to NYC on December 20"

  # Specify Whisper model
  python voice_to_flight_integrated.py --model models/ggml-tiny.en.bin

  # Custom voice timeout
  python voice_to_flight_integrated.py --timeout 15000
"""

import os
import sys
import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import flight search functionality
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


class VoiceToFlightSearch:
    """Integrated voice-to-flight search application"""

    def __init__(self,
                 google_api_key: str,
                 amadeus_key: str,
                 amadeus_secret: str,
                 voice_to_text_binary: str = "./voice-to-text-mcp",
                 whisper_model: str = "models/ggml-base.en.bin"):
        self.google_api_key = google_api_key
        self.amadeus_key = amadeus_key
        self.amadeus_secret = amadeus_secret
        self.amadeus_token = None
        self.voice_to_text_binary = voice_to_text_binary
        self.whisper_model = whisper_model

        if GEMINI_AVAILABLE:
            genai.configure(api_key=google_api_key)
            self.model = genai.GenerativeModel('gemini-pro')

    def capture_voice(self, timeout_ms: int = 30000, silence_timeout_ms: int = 2000) -> Optional[str]:
        """Capture voice input and transcribe using Whisper"""
        print("\n🎤 Starting voice recording...")
        print(f"Speak your flight search query now (max {timeout_ms/1000}s)")
        print("Recording will stop automatically after silence or timeout")
        print("-" * 60)

        try:
            # Run voice-to-text binary
            cmd = [
                self.voice_to_text_binary,
                "--timeout-ms", str(timeout_ms),
                "--silence-timeout-ms", str(silence_timeout_ms),
                self.whisper_model
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_ms / 1000 + 10  # Add buffer for processing
            )

            if result.returncode == 0:
                # Extract transcription from output
                transcription = result.stdout.strip()
                # Remove any debug messages
                lines = transcription.split('\n')
                # Get the last non-empty line (likely the transcription)
                for line in reversed(lines):
                    if line.strip() and not line.startswith('[') and not line.startswith('Recording'):
                        return line.strip()
                return transcription
            else:
                print(f"❌ Voice capture failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print("⏱️ Voice recording timed out")
            return None
        except FileNotFoundError:
            print(f"❌ Voice-to-text binary not found: {self.voice_to_text_binary}")
            print("Please ensure the Rust binary is built and available")
            return None
        except Exception as e:
            print(f"❌ Voice capture error: {e}")
            return None

    def parse_query(self, query: str) -> Dict[str, Any]:
        """Use Gemini to parse natural language query into structured params"""
        if not GEMINI_AVAILABLE:
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
            print(f"⚠️ Gemini parsing failed: {e}")
            print("Falling back to simple parsing...")
            return self._simple_parse(query)

    def _simple_parse(self, query: str) -> Dict[str, Any]:
        """Simple fallback parser without AI"""
        words = query.upper().split()

        # Look for airport codes (3 uppercase letters)
        codes = [w for w in words if len(w) == 3 and w.isalpha()]

        # Look for dates
        dates = []
        for word in words:
            if any(month in word.upper() for month in ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                                                         'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']):
                dates.append(word)

        return {
            "originLocationCode": codes[0] if len(codes) > 0 else "LAX",
            "destinationLocationCode": codes[1] if len(codes) > 1 else "JFK",
            "departureDate": "2025-12-20",  # Default date
            "returnDate": None,  # One-way by default
            "adults": 1,
            "travelClass": "ECONOMY"
        }

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
            print(f"❌ Amadeus API Error: {e}")
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
                print(f"⚠️ Error formatting flight {idx}: {e}")
                continue

        return results

    def display_results(self, results: list):
        """Display flight results"""
        if not results:
            print("\n❌ No flights found. Try different dates or airports.")
            return

        print("\n" + "=" * 60)
        print("✈️  FLIGHT SEARCH RESULTS")
        print("=" * 60)

        for flight in results:
            print(f"\n✈️  Flight #{flight['number']}")
            print(f"  💰 Price: {flight['price']}")
            print(f"  🏢 Carrier: {flight['carrier']}")
            print(f"  🛫 Departure: {flight['departure']['airport']} at {flight['departure']['time']}")
            print(f"  🛬 Arrival: {flight['arrival']['airport']} at {flight['arrival']['time']}")
            print(f"  ⏱️  Duration: {flight['duration']}")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Voice-to-Flight Search for ARM Tablets")
    parser.add_argument("--text", type=str, help="Text query (bypass voice input)")
    parser.add_argument("--model", type=str, default="models/ggml-base.en.bin", help="Whisper model path")
    parser.add_argument("--timeout", type=int, default=30000, help="Voice recording timeout (ms)")
    parser.add_argument("--silence-timeout", type=int, default=2000, help="Silence detection timeout (ms)")
    parser.add_argument("--voice-binary", type=str, default="./voice-to-text-mcp", help="Path to voice-to-text binary")
    args = parser.parse_args()

    # Check API keys
    google_key = os.getenv("GOOGLE_API_KEY")
    amadeus_key = os.getenv("AMADEUS_API_KEY")
    amadeus_secret = os.getenv("AMADEUS_API_SECRET")

    if not google_key:
        print("⚠️ Warning: GOOGLE_API_KEY not set in .env file")
        print("AI parsing will be unavailable (using fallback)")

    if not amadeus_key or not amadeus_secret:
        print("❌ Error: Amadeus API credentials not set in .env file")
        return 1

    # Initialize application
    app = VoiceToFlightSearch(
        google_key or "",
        amadeus_key,
        amadeus_secret,
        voice_to_text_binary=args.voice_binary,
        whisper_model=args.model
    )

    print("\n" + "=" * 60)
    print("🎤 ✈️  VOICE-TO-FLIGHT SEARCH (ARM64)")
    print("=" * 60)

    # Get query (voice or text)
    if args.text:
        query = args.text
        print(f"\n📝 Text mode: {query}")
    else:
        # Check if voice-to-text binary exists
        if not Path(args.voice_binary).exists():
            print(f"\n❌ Voice-to-text binary not found: {args.voice_binary}")
            print("Please build the Rust binary or use --text mode")
            return 1

        # Check if model exists
        if not Path(args.model).exists():
            print(f"\n❌ Whisper model not found: {args.model}")
            print("Please download a model or specify --model path")
            return 1

        query = app.capture_voice(
            timeout_ms=args.timeout,
            silence_timeout_ms=args.silence_timeout
        )

        if not query:
            print("\n❌ No voice input captured. Exiting.")
            return 1

        print(f"\n🎤 Transcribed: \"{query}\"")

    # Parse query
    print("\n🔍 Parsing flight requirements...")
    params = app.parse_query(query)
    print("\n📋 Extracted parameters:")
    print(json.dumps(params, indent=2))

    # Search flights
    print("\n🔎 Searching for flights...")
    results = app.search_flights(params)

    # Display results
    app.display_results(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
