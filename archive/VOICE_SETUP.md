# Voice-to-Text Integration Setup Guide

This guide shows how to add voice input capabilities to the flight search agent using the Model Context Protocol (MCP).

## Architecture

```
User speaks → Voice-to-Text MCP Server → Transcribed Text → Flight Search Agent → Results
```

## Prerequisites

1. **Rust** (for building the MCP server)
2. **Microphone** (for voice input)
3. **Python 3.8+** (for the flight search agent)

## Step 1: Install Rust

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Reload shell configuration
source $HOME/.cargo/env

# Verify installation
cargo --version
```

## Step 2: Build the Voice-to-Text MCP Server

The MCP server is already cloned in `voice-to-text-mcp/`. Build it:

```bash
cd voice-to-text-mcp

# Build the release version (takes 2-3 minutes on first build)
cargo build --release

# Verify the binary was created
ls -lh target/release/voice-to-text-mcp
```

## Step 3: Download Whisper Model

Download the Whisper model for speech recognition:

```bash
# Still in voice-to-text-mcp/ directory
./scripts/download-models.sh
```

**Interactive Menu Options:**
- For **development/testing**: Choose `ggml-tiny.en.bin` (75MB, fastest)
- For **general use**: Choose `ggml-base.en.bin` (142MB, recommended ⭐)
- For **high quality**: Choose `ggml-small.en.bin` (466MB, best accuracy)

**Manual Download (alternative):**
```bash
cd models/
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
cd ..
```

## Step 4: Test the MCP Server (Optional)

Test that the MCP server works correctly:

```bash
# Test voice recording (records for 30s or stops after 2s of silence)
./target/release/voice-to-text-mcp models/ggml-base.en.bin

# Test with debug mode (saves audio files)
./target/release/voice-to-text-mcp --debug models/ggml-base.en.bin
```

Return to the main project directory:
```bash
cd ..
```

## Step 5: Use Voice Input with Flight Search

### Basic Voice Input

```bash
# Use voice input to search for flights
python3 flight_search_vtt.py --voice
```

**What happens:**
1. You'll see: `🎤 Listening... (max 30s, silence timeout 2s)`
2. Speak your flight requirement (e.g., "Find a round trip flight from New York to Los Angeles on December 15th returning December 22nd for 2 passengers")
3. After 2 seconds of silence, recording stops automatically
4. The speech is transcribed to text
5. The interpreter agent parses it into structured parameters
6. The executor agent searches for flights

### Voice with Custom Timeout

```bash
# Record for up to 45 seconds
python3 flight_search_vtt.py --voice --voice-timeout 45000

# Record with longer silence timeout (5 seconds)
python3 flight_search_vtt.py --voice --voice-silence-timeout 5000
```

### Voice with Debug Output

```bash
# See detailed debug information
python3 flight_search_vtt.py --voice --debug --verbose
```

### Text Input (No Voice)

```bash
# Use text query instead of voice
python3 flight_search_vtt.py --query "Find flights from LAX to NYC on Dec 15"
```

## File Reference

### Core Files

- **[flight_search_vtt.py](flight_search_vtt.py)** - Main flight search with voice integration
- **[voice_mcp_client.py](voice_mcp_client.py)** - Python MCP client for voice-to-text
- **voice-to-text-mcp/** - MCP server (Rust-based)

### Voice MCP Client API

The `VoiceToTextMCPClient` class provides:

```python
from voice_mcp_client import VoiceToTextMCPClient

# Initialize
client = VoiceToTextMCPClient(
    mcp_server_path="voice-to-text-mcp/target/release/voice-to-text-mcp",
    model_path="voice-to-text-mcp/models/ggml-base.en.bin"
)

# Record and transcribe
text = client.listen(
    timeout_ms=30000,         # Max recording time
    silence_timeout_ms=2000,  # Stop after 2s silence
    auto_stop=True            # Auto-stop on silence
)

# Transcribe existing audio file
text = client.transcribe_file("audio.wav")
```

## Command Reference

### flight_search_vtt.py Options

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

## Tips for Best Results

### Voice Input Best Practices

1. **Speak clearly** in a quiet environment
2. **State complete information**:
   - Origin and destination cities
   - Travel dates (be specific: "December 15th 2025")
   - Number of passengers
   - Class preference if any

3. **Example good voice inputs**:
   - "Find a round trip from Atlanta to New York, departing December 1st, returning December 15th, for 2 adults in economy"
   - "I need a flight from San Francisco to Chicago on January 10th, one way, business class"
   - "Search for flights from LAX to JFK, leaving next Friday, returning the following Monday"

### Model Selection

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| ggml-tiny.en.bin | 75MB | Very Fast | Good | Quick testing, prototyping |
| ggml-base.en.bin | 142MB | Fast | Better | General use (recommended) |
| ggml-small.en.bin | 466MB | Slower | Best | High accuracy needs |

### Timeout Settings

```bash
# Quick commands (10 seconds)
--voice-timeout 10000 --voice-silence-timeout 1000

# Normal use (30 seconds)
--voice-timeout 30000 --voice-silence-timeout 2000

# Detailed descriptions (60 seconds)
--voice-timeout 60000 --voice-silence-timeout 3000
```

## Troubleshooting

### "cargo: command not found"

Install Rust: https://rustup.rs/

### "MCP server binary not found"

Build the server:
```bash
cd voice-to-text-mcp && cargo build --release
```

### "Whisper model not found"

Download the model:
```bash
cd voice-to-text-mcp && ./scripts/download-models.sh
```

### "No input device available"

Check that your microphone is:
- Connected and working
- Not being used by another application
- Allowed in system privacy settings (macOS: System Settings > Privacy & Security > Microphone)

### "voice_mcp_client not available"

Make sure `voice_mcp_client.py` is in the same directory as `flight_search_vtt.py`.

### Poor Transcription Quality

Try:
1. Use a better quality model (`ggml-small.en.bin`)
2. Speak more clearly and slowly
3. Reduce background noise
4. Increase silence timeout for longer pauses

## Integration with Other Projects

The voice-to-text MCP server can be integrated with any Python project:

```python
from voice_mcp_client import VoiceToTextMCPClient

# Initialize client
client = VoiceToTextMCPClient(
    "voice-to-text-mcp/target/release/voice-to-text-mcp",
    "voice-to-text-mcp/models/ggml-base.en.bin"
)

# Get voice input
user_input = client.listen(timeout_ms=30000)

# Use the transcribed text in your application
process_command(user_input)
```

## MCP Architecture

This integration follows the Model Context Protocol (MCP) standard:

1. **MCP Server** (Rust): Handles audio capture and Whisper transcription
2. **MCP Client** (Python): Communicates with server via JSON-RPC
3. **Flight Agent** (Python): Uses transcribed text for flight search

Benefits of MCP:
- **Language-agnostic**: Server in Rust, client in Python
- **Standardized protocol**: Works with any MCP-compatible tools
- **Isolated concerns**: Audio processing separate from business logic
- **Reusable**: Same MCP server can be used by multiple clients

## References

- Voice-to-Text MCP: https://github.com/acazau/voice-to-text-mcp
- Model Context Protocol: https://modelcontextprotocol.io/
- Whisper Models: https://huggingface.co/ggerganov/whisper.cpp
