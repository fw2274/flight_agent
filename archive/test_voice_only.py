#!/usr/bin/env python3
"""
Simple test script for voice-to-text MCP integration.
Tests just the voice transcription without the full flight search.
"""

import sys
from voice_mcp_client import VoiceToTextMCPClient

def main():
    print("=" * 60)
    print("🎤 Voice-to-Text Test")
    print("=" * 60)
    print()

    try:
        # Initialize MCP client
        print("Initializing voice-to-text client...")
        client = VoiceToTextMCPClient(
            "voice-to-text-mcp/target/release/voice-to-text-mcp",
            "voice-to-text-mcp/models/ggml-base.en.bin"
        )
        print("✓ Client initialized")
        print()

        # Record and transcribe
        print("Recording will start in 3 seconds...")
        print("Speak clearly: 'Find a flight from New York to Los Angeles'")
        print()

        import time
        time.sleep(3)

        text = client.listen(timeout_ms=30000, silence_timeout_ms=2000)

        if text:
            print()
            print("=" * 60)
            print("✅ SUCCESS - Transcription:")
            print("=" * 60)
            print(text)
            print("=" * 60)
            print()
            print("This text would be passed to the flight search agent.")
        else:
            print()
            print("❌ No speech detected")
            print("Tips:")
            print("  - Make sure your microphone is working")
            print("  - Check microphone permissions (System Settings > Privacy)")
            print("  - Try speaking louder or closer to the mic")

    except FileNotFoundError as e:
        print(f"\n❌ Setup Error: {e}")
        print("\nMake sure you've completed the setup:")
        print("  1. cd voice-to-text-mcp")
        print("  2. cargo build --release")
        print("  3. Download model: ./scripts/download-models.sh")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
