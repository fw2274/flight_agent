# Quick Reference - Voice-to-Text Flight Search

## One-Time Setup (5 minutes)

```bash
# 1. Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# 2. Build MCP server & download model
cd voice-to-text-mcp
cargo build --release
./scripts/download-models.sh  # Choose option 2: ggml-base.en.bin
cd ..

# 3. Verify everything works
./test_voice_setup.sh
```

## Daily Usage

### Voice Input 🎤
```bash
# Basic voice search
python3 flight_search_vtt.py --voice

# Longer recording time (45 seconds)
python3 flight_search_vtt.py --voice --voice-timeout 45000

# More patient silence detection (5 seconds)
python3 flight_search_vtt.py --voice --voice-silence-timeout 5000
```

### Text Input ⌨️
```bash
# Traditional text query
python3 flight_search_vtt.py --query "Find flights from LAX to NYC on Dec 15"

# With debug output
python3 flight_search_vtt.py --query "..." --debug --verbose
```

## What to Say (Voice Examples)

Good voice inputs:
- ✅ "Find a round trip from Atlanta to New York, December first to December fifteenth, two adults, economy"
- ✅ "I need a one-way flight from San Francisco to Chicago on January tenth, business class"
- ✅ "Search for flights from LAX to JFK next Friday, returning the following Monday"

Too vague:
- ❌ "Find me a flight" (missing origin, destination, dates)
- ❌ "Go to New York" (missing origin, departure date)

## Command Options

| Flag | Default | Description |
|------|---------|-------------|
| `--voice` | - | Enable voice input |
| `--voice-timeout` | 30000 | Max recording time (ms) |
| `--voice-silence-timeout` | 2000 | Stop after silence (ms) |
| `--query` | - | Text query instead of voice |
| `--debug` | false | Show event timeline |
| `--verbose` | false | Show tool calls |

## Troubleshooting

### "cargo: command not found"
```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### "MCP server binary not found"
```bash
cd voice-to-text-mcp && cargo build --release && cd ..
```

### "Whisper model not found"
```bash
cd voice-to-text-mcp && ./scripts/download-models.sh && cd ..
```

### "No input device available"
- Check microphone is connected and not in use
- On macOS: System Settings > Privacy & Security > Microphone

### Poor transcription quality
- Use better model: `ggml-small.en.bin`
- Speak more clearly and slowly
- Reduce background noise
- Increase silence timeout: `--voice-silence-timeout 5000`

## File Locations

| File | Purpose |
|------|---------|
| `flight_search_vtt.py` | Main voice-enabled flight search |
| `voice_mcp_client.py` | Python MCP client |
| `voice-to-text-mcp/target/release/voice-to-text-mcp` | MCP server binary |
| `voice-to-text-mcp/models/ggml-base.en.bin` | Whisper model |
| `.env` | API keys (GOOGLE_API_KEY, AMADEUS_API_KEY, etc.) |

## Model Comparison

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| ggml-tiny.en.bin | 75MB | Fastest | Testing |
| ggml-base.en.bin | 142MB | Fast | Daily use ⭐ |
| ggml-small.en.bin | 466MB | Slower | High accuracy |

## Common Patterns

### Quick test
```bash
python3 flight_search_vtt.py --voice --voice-timeout 15000
```

### Detailed description
```bash
python3 flight_search_vtt.py --voice --voice-timeout 60000 --voice-silence-timeout 3000
```

### Fallback to text
```bash
python3 flight_search_vtt.py --query "Find flights from ATL to JFK on 2025-12-01"
```

### Debug mode
```bash
python3 flight_search_vtt.py --voice --debug --verbose
```

## API Error Codes

The enhanced error handling now shows specific error codes from Amadeus API:

| Code | Meaning | Solution |
|------|---------|----------|
| 38192 | No flights found | Try different dates/airports |
| 32171 | Invalid airport code | Use valid IATA codes (e.g., "LAX") |
| 4926 | Invalid date format | Use YYYY-MM-DD format |
| 38190 | Date in the past | Use future dates |

## Resources

- **Full Setup Guide**: [VOICE_SETUP.md](VOICE_SETUP.md)
- **Integration Summary**: [VOICE_INTEGRATION_SUMMARY.md](VOICE_INTEGRATION_SUMMARY.md)
- **Voice-to-Text MCP**: https://github.com/acazau/voice-to-text-mcp
- **Verify Setup**: Run `./test_voice_setup.sh`

## Support

1. Check this quick reference first
2. Read [VOICE_SETUP.md](VOICE_SETUP.md) for detailed instructions
3. Run `./test_voice_setup.sh` to diagnose setup issues
4. Check the troubleshooting section above
