# Multi-Agent Voice-Activated Flight Search System

A comprehensive flight search agent with voice input capabilities using Google ADK, Amadeus API, LangGraph, and Model Context Protocol (MCP).

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Voice Integration Setup](#voice-integration-setup)
- [Usage Guide](#usage-guide)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)
- [Integration Examples](#integration-examples)

---

## Overview

This project investigates the changes needed to port a multi-agent application to mobile application running on ARM architectures. We also investigate the ability of claude code to convert a multi-agent application implemented using Google ADK and mcp server connections to run on arm architectures. The multi-agent project was initially developed as capstoneproject for this competition https://www.kaggle.com/competitions/agents-intensive-capstone-project. We modified the submitted code on this repo https://github.com/fw2274/flight_agent/tree/main using claude code to work on arm architectures. 

# Voice-to-Flight Search System Explanation

This Python application creates an integrated voice-controlled flight search system designed for ARM tablets. It combines multiple technologies to let users speak their flight queries naturally and get real-time results.

## Core Workflow

The system follows a four-stage pipeline:

1. **Voice Input** → User speaks their flight request
2. **Whisper Transcription** → Converts speech to text using a local Whisper model
3. **Gemini Parsing** → AI extracts structured flight parameters from natural language
4. **Amadeus Search** → Queries the Amadeus API for actual flight offers

## Key Components

### VoiceToFlightSearch Class

The main application class that orchestrates the entire process.

**`capture_voice()`** - Records audio and transcribes it by calling an external Rust binary (`voice-to-text-mcp`) that handles the actual Whisper processing. It manages timeouts and silence detection, returning the transcribed text.

**`parse_query()`** - Takes the transcribed text and uses Google's Gemini AI to extract structured information like airport codes, dates, passenger count, and travel class. If Gemini fails, it falls back to a simple pattern-matching parser that looks for airport codes and date keywords.

**`search_flights()`** - Authenticates with Amadeus using OAuth2 credentials, then queries their flight search API with the parsed parameters. It handles API responses and formats the data for display.

**`display_results()`** - Presents flight options with price, carrier, departure/arrival times, and duration in a formatted console output.

## Usage Modes

The application supports two modes:

- **Voice mode** (default): Captures live audio input for hands-free operation
- **Text mode** (`--text` flag): Accepts typed queries for testing without voice hardware

## Technical Architecture

The code is designed for ARM architecture (like tablets) and uses external dependencies carefully, checking for their availability before use. It loads credentials from environment variables (.env file) and provides graceful degradation when optional components aren't available.

The Whisper model runs locally for privacy and offline capability, while Gemini and Amadeus require internet connectivity for AI parsing and live flight data.


### System Flow

```
┌─────────────────┐
│  User speaks    │
│  flight query   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Voice-to-Text MCP Server│  ← Rust-based, uses Whisper AI
│ (Rust + Whisper)        │
└────────┬────────────────┘
         │
         ▼ (JSON-RPC)
┌─────────────────────────┐
│ voice_mcp_client.py     │  ← Python MCP client
│ (Python MCP Client)     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ flight_search_vtt.py    │  ← Enhanced flight search
│ (Interpreter + Executor)│
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ LangGraph Flight Search │  ← Existing Amadeus integration
│ (agent_graph.py)        │
└─────────────────────────┘
```

### Key Capabilities
- 🎤 **Voice Input**: Speak your flight requirements naturally
- 💬 **Text Input**: Traditional text query support
- 🤖 **Dual-Agent System**: Interpreter agent + Executor agent
- ✈️ **Real Flight Data**: Amadeus API integration
- 🧠 **Smart Parsing**: Gemini AI for natural language understanding
- 🎯 **Accurate Results**: Structured flight search with IATA codes and ISO dates

---

## Quick Start

### Text Input Mode

**Prerequisites:**
- Python 3.10+
- Amadeus API credentials ([Get them here](https://developers.amadeus.com/))
- Google API key

**Setup:**
```bash
# 1. Setup environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure credentials
echo "GOOGLE_API_KEY=your_key_here" >> .env
echo "AMADEUS_API_KEY=your_key_here" >> .env
echo "AMADEUS_API_SECRET=your_secret_here" >> .env

# 3. Run test search
python flight_search.py --query "Find a round-trip flight from ATL to JFK on Dec 02 returning Dec 15 for 2 adults in economy"
```

**Flags:** `--verbose` (stream tool calls), `--debug` (full timeline)

### Voice Input Mode

**Additional Prerequisites:**
- Rust
- Microphone
- ~200MB disk space for Whisper model

**Setup:**
```bash
# 1. Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# 2. Build voice-to-text MCP server
cd voice-to-text-mcp
cargo build --release
./scripts/download-models.sh  # Choose ggml-base.en.bin
cd ..

# 3. Verify setup
./test_voice_setup.sh

# 4. Test voice input
python3 flight_search_vtt.py --voice
```

**What to say:**
- "Find a round trip from Atlanta to New York, December first to December fifteenth, two adults, economy"
- "I need a flight from San Francisco to Chicago on January tenth, business class"

---

## System Architecture

### Three-Agent Architecture

**Agent 1: Voice Recognition Agent**
- Captures spoken input from users and converts it into text
- Technology: Whisper AI via MCP server (Rust-based)
- Hardware acceleration: Metal/CoreML (macOS), CUDA (Linux/Windows)

**Agent 2: Information Extraction Agent**
- Processes transcribed text and extracts structured parameters
- Model: Gemini 2.5 Flash Lite
- Extracts:
  - Origin and destination cities/airports (IATA codes)
  - Departure and return dates (ISO format)
  - Number of passengers (adults, children, infants)
  - Cabin class preferences
  - Special requirements or preferences

**Agent 3: Flight Search Agent**
- Executes flight search based on structured information
- Framework: LangGraph
- API: Amadeus (real flight data)
- Output: Flight options with prices, times, airlines, duration

### Component Details

The Amadeus tooling comes from `langgraph_travel_agent` (vendored under `langgraph_travel_agent/backend`). We wrap its `agent_graph.py` primitives so Google ADK can call them directly:
- `agent_graph_module.search_flights` → exposed to ADK via async `search_flights` wrapper
- `agent_graph_module.amadeus` client → validated on startup

**Files you'll care about:**
- [flight_search.py](flight_search.py) — main entry; wires Gemini to LangGraph tool (text input only)
- [flight_search_vtt.py](flight_search_vtt.py) — flight search with voice-to-text integration
- [voice_mcp_client.py](voice_mcp_client.py) — Python client for voice-to-text MCP server
- [langgraph_travel_agent/backend/agent_graph.py](langgraph_travel_agent/backend/agent_graph.py) — search_flights LangChain tool and Amadeus plumbing
- `voice-to-text-mcp/` — Rust-based MCP server for speech recognition

---

## Voice Integration Setup

### Step 1: Install Rust

```bash
# Install Rust via rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Reload shell configuration
source $HOME/.cargo/env

# Verify installation
cargo --version
# Expected: cargo 1.91.1 (or later)
```

### Step 2: Build MCP Server

```bash
cd voice-to-text-mcp

# Build release version (takes 2-3 minutes first time)
cargo build --release

# Verify binary was created
ls -lh target/release/voice-to-text-mcp
# Expected: ~4.5MB binary

cd ..
```

### Step 3: Download Whisper Model

Choose the right model for your needs:

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| ggml-tiny.en.bin | 75MB | Very Fast | Good | Testing, prototyping |
| ggml-base.en.bin | 142MB | Fast | Better | **General use (recommended)** ⭐ |
| ggml-small.en.bin | 466MB | Slower | Best | High accuracy needs |

**Interactive download:**
```bash
cd voice-to-text-mcp
./scripts/download-models.sh
# Choose: ggml-base.en.bin
cd ..
```

**Manual download:**
```bash
cd voice-to-text-mcp/models/
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
cd ../..
```

### Step 4: Verify Setup

```bash
./test_voice_setup.sh
```

**What it checks:**
- ✓ Rust installation (cargo)
- ✓ MCP repository presence
- ✓ Binary build status
- ✓ Whisper model availability
- ✓ Python integration files
- ✓ Environment variables

### Step 5: Test Voice Input

```bash
# Basic voice input test
python3 flight_search_vtt.py --voice

# Voice with debug output
python3 flight_search_vtt.py --voice --debug --verbose
```

**Expected flow:**
1. `🎤 Listening... (max 30s, silence timeout 2s)`
2. Speak your flight requirement
3. Recording stops after 2 seconds of silence
4. Transcription appears
5. Interpreter parses parameters
6. Executor searches flights
7. Results displayed

---

## Usage Guide

### Command Reference

**flight_search_vtt.py options:**
```
--voice                     Enable voice input
--voice-timeout N           Recording timeout in milliseconds (default: 30000)
--voice-silence-timeout N   Silence timeout in milliseconds (default: 2000)
--mcp-server PATH          Path to MCP server binary
--mcp-model PATH           Path to Whisper model
--query TEXT               Use text query instead of voice
--debug                    Show debug timeline
--verbose                  Show tool calls/responses
```

### Voice Input Best Practices

**For best transcription results:**

1. **Environment**: Speak in a quiet room, reduce background noise
2. **Speaking style**: Speak clearly at normal pace, use complete sentences
3. **Dates**: State dates explicitly ("December fifteenth" not "12/15")
4. **Pauses**: Pause briefly between thoughts (silence detection helps)

**Example good inputs:**
```
"Find a round trip from Atlanta to New York,
 departing December 1st, returning December 15th,
 for 2 adults in economy"

"I need a flight from San Francisco to Chicago
 on January 10th, one way, business class"

"Search for flights from LAX to JFK,
 leaving next Friday, returning the following Monday"
```

### Timeout Configuration

```bash
# Quick commands (10 seconds)
python3 flight_search_vtt.py --voice --voice-timeout 10000 --voice-silence-timeout 1000

# Normal use (30 seconds) - DEFAULT
python3 flight_search_vtt.py --voice --voice-timeout 30000 --voice-silence-timeout 2000

# Detailed descriptions (60 seconds)
python3 flight_search_vtt.py --voice --voice-timeout 60000 --voice-silence-timeout 3000
```

### Example Session

```bash
$ python3 flight_search_vtt.py --voice

🎤 Listening... (max 30s, silence timeout 2s)
   Speak your flight requirement now!

# User says: "Find a round trip from Atlanta to New York,
#             departing December 1st, returning December 15th,
#             for 2 adults in economy"

✓ Transcribed: 'Find a round trip from Atlanta to New York,
departing December 1st, returning December 15th,
for 2 adults in economy'

🧭 Interpreter Agent

✓ Interpreter output:
{
  "originLocationCode": "ATL",
  "destinationLocationCode": "JFK",
  "departureDate": "2025-12-01",
  "returnDate": "2025-12-15",
  "adults": 2,
  "travelClass": "ECONOMY"
}

🛠️  Executor Agent

→ Flight search: ATL → JFK
  Departure: 2025-12-01, Return: 2025-12-15, Adults: 2, Class: ECONOMY

✓ Received 3 flight results

📋 FLIGHT SEARCH RESULTS
[Flight options listed here...]

✅ Search complete!
```

---

## Technical Details

### MCP (Model Context Protocol) Architecture

**What is MCP?**
- Language-agnostic communication protocol
- JSON-RPC 2.0 based
- Enables tools to work across different languages

**Communication:**
- Transport: stdio (stdin/stdout)
- Protocol: JSON-RPC 2.0
- Tools exposed: `listen`, `transcribe_file`

**Benefits:**
- Language-agnostic (Rust server, Python client)
- Standardized protocol
- Isolated concerns (audio processing separate from business logic)
- Reusable components

### Voice Processing

**Whisper AI Integration:**
- OpenAI Whisper (speech recognition)
- Quantized models (ggml format)
- English-only variants (.en suffix)

**Hardware Acceleration:**
- macOS: Metal GPU + CoreML (Apple Neural Engine)
- Linux/Windows: CUDA (NVIDIA GPUs)
- Fallback: CPU-only

**Recording format:**
- Sample rate: 16kHz
- Channels: Mono
- Format: WAV (PCM)

**Auto-stop logic:**
- Records up to `timeout_ms` milliseconds
- Stops early if `silence_timeout_ms` of silence detected
- Silence threshold: -30dB

### Google ADK Integration

**Agent configuration:**
```python
# Interpreter Agent
model = "gemini-2.5-flash-lite"
temperature = 0.3  # Low for consistent parsing

# Executor Agent
model = "gemini-2.5-flash-lite"
tools = [search_flights]
```

### LangGraph Integration

**Key file:** [langgraph_travel_agent/backend/agent_graph.py](langgraph_travel_agent/backend/agent_graph.py)

**Enhanced error handling:**
```python
except ResponseError as error:
    error_code = getattr(error, 'code', 'UNKNOWN')
    error_description = getattr(error, 'description', str(error))

    # Extract from response body
    if hasattr(error, 'response') and error.response:
        error_body = error.response.body
        if isinstance(error_body, dict):
            errors = error_body.get('errors', [])
            if errors:
                first_error = errors[0]
                error_code = first_error.get('code', error_code)
                error_description = first_error.get('detail', error_description)
```

---

## Troubleshooting

### Setup Issues

**"cargo: command not found"**
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

**"MCP server binary not found"**
```bash
cd voice-to-text-mcp && cargo build --release
```

**"Whisper model not found"**
```bash
cd voice-to-text-mcp && ./scripts/download-models.sh
```

**Missing API keys**
```bash
# Check .env file exists
cat .env

# Verify all keys are set
grep GOOGLE_API_KEY .env
grep AMADEUS_API_KEY .env
grep AMADEUS_API_SECRET .env
```

### Voice Input Issues

**"No input device available"**

Checklist:
- Microphone is connected and working
- Microphone is not in use by another application
- System has microphone permissions

**macOS:**
```
System Settings → Privacy & Security → Microphone
Ensure Terminal has access
```

**Linux:**
```bash
# Check audio devices
arecord -l

# Test microphone
arecord -d 5 test.wav
aplay test.wav
```

**"Recording cuts off too early"**
```bash
# Increase silence timeout
python3 flight_search_vtt.py --voice --voice-silence-timeout 5000

# Increase overall timeout
python3 flight_search_vtt.py --voice --voice-timeout 45000
```

**"Poor transcription quality"**

Try:
1. Use a better model (ggml-small.en.bin)
2. Speak more clearly and slowly
3. Reduce background noise
4. Increase silence timeout for longer pauses

### Flight Search Issues

**"No results returned"**

Checklist:
- Dates are in the future
- Origin/destination are valid IATA codes or city names
- Travel dates are realistic

**Debug:**
```bash
python3 flight_search_vtt.py --query "Your query" --debug --verbose
```

**Common Amadeus API error codes:**

- **38194**: Invalid origin/destination → Use valid IATA codes (e.g., `ATL`, `JFK`)
- **477**: Invalid date format → Use `YYYY-MM-DD` format
- **4926**: No flights available → Try different dates or route
- **38187**: Invalid passenger count → Check adults/children/infants counts

---

## Integration Examples

### Using the MCP Client in Other Projects

The [voice_mcp_client.py](voice_mcp_client.py) can be used in any Python project:

```python
from voice_mcp_client import VoiceToTextMCPClient

# Initialize client
client = VoiceToTextMCPClient(
    mcp_server_path="voice-to-text-mcp/target/release/voice-to-text-mcp",
    model_path="voice-to-text-mcp/models/ggml-base.en.bin"
)

# Listen for voice input
user_input = client.listen(
    timeout_ms=30000,         # 30 seconds max
    silence_timeout_ms=2000,  # Stop after 2s silence
    auto_stop=True            # Enable auto-stop
)

print(f"User said: {user_input}")

# Transcribe existing audio file
transcript = client.transcribe_file("audio.wav")
print(f"Transcription: {transcript}")
```

### Custom Flight Search Workflow

```python
from voice_mcp_client import VoiceToTextMCPClient
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize voice client
voice_client = VoiceToTextMCPClient(
    "voice-to-text-mcp/target/release/voice-to-text-mcp",
    "voice-to-text-mcp/models/ggml-base.en.bin"
)

# Get voice input
print("🎤 Speak your flight requirement...")
query = voice_client.listen(timeout_ms=30000)
print(f"✓ Heard: {query}")

# Process with your custom agent
# ... your code here ...
```

### References

**Official Documentation:**
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Google ADK](https://ai.google.dev/)
- [Amadeus for Developers](https://developers.amadeus.com/)

**Related Projects:**
- [Voice-to-Text MCP](https://github.com/acazau/voice-to-text-mcp)
- [Whisper AI](https://github.com/openai/whisper)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- [LangGraph Travel Agent](https://github.com/fw2274/flight_agent)

**Whisper Models:**
- [Hugging Face Models](https://huggingface.co/ggerganov/whisper.cpp)

---

**Happy flying!** ✈️🎤


