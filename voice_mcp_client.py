"""
MCP Client for Voice-to-Text Integration
Connects to the voice-to-text MCP server and provides voice input capabilities.

Based on the voice-to-text-mcp repository: https://github.com/acazau/voice-to-text-mcp
"""

import json
import subprocess
import sys
from typing import Optional, Dict, Any
from pathlib import Path


class VoiceToTextMCPClient:
    """
    Client for voice-to-text MCP server.

    Provides methods to:
    - Record voice and transcribe (listen)
    - Transcribe existing audio files
    - Configure recording parameters
    """

    def __init__(self, mcp_server_path: str, model_path: str):
        """
        Initialize the MCP client.

        Args:
            mcp_server_path: Path to the voice-to-text-mcp binary
            model_path: Path to the Whisper model file
        """
        self.mcp_server_path = Path(mcp_server_path)
        self.model_path = Path(model_path)

        # Validate paths
        if not self.mcp_server_path.exists():
            raise FileNotFoundError(
                f"MCP server binary not found: {self.mcp_server_path}\n"
                f"Please build it first:\n"
                f"  cd voice-to-text-mcp && cargo build --release"
            )

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Whisper model not found: {self.model_path}\n"
                f"Please download it first:\n"
                f"  cd voice-to-text-mcp && ./scripts/download-models.sh"
            )

    def _call_mcp_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call an MCP tool via JSON-RPC with proper MCP protocol initialization.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool response
        """
        try:
            # Start MCP server process
            process = subprocess.Popen(
                [
                    str(self.mcp_server_path),
                    "--mcp-server",
                    str(self.model_path)
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )

            # Step 1: Send MCP initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "voice-to-text-client",
                        "version": "1.0.0"
                    }
                }
            }

            process.stdin.write(json.dumps(init_request) + "\n")
            process.stdin.flush()

            # Read initialization response
            init_response = process.stdout.readline()

            # Step 2: Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }

            process.stdin.write(json.dumps(initialized_notification) + "\n")
            process.stdin.flush()

            # Step 3: Send tool call request
            tool_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {}
                }
            }

            process.stdin.write(json.dumps(tool_request) + "\n")
            process.stdin.flush()
            # Don't close stdin yet - keep connection open while recording

            # Read tool response (this blocks until recording completes)
            # The listen tool can take up to timeout_ms + processing time
            tool_response_line = None
            max_wait = (arguments.get("timeout_ms", 30000) / 1000) + 30  # recording time + 30s processing
            import time
            start_time = time.time()

            while True:
                # Check timeout
                if time.time() - start_time > max_wait:
                    raise TimeoutError(f"MCP call exceeded {max_wait}s timeout")

                line = process.stdout.readline()
                if not line:
                    # No more output - check if process ended
                    if process.poll() is not None:
                        break
                    continue

                line = line.strip()
                if not line:
                    continue

                try:
                    response = json.loads(line)
                    if response.get("id") == 1:
                        tool_response_line = response
                        break
                except json.JSONDecodeError:
                    # Not JSON, might be debug output - skip it
                    continue

            # Now close stdin and cleanup
            try:
                process.stdin.close()
            except:
                pass

            # Don't try to read all stderr - it might block
            # Just terminate the process
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                process.kill()
                process.wait()

            # Parse response
            if not tool_response_line:
                raise RuntimeError("No valid JSON-RPC response received")

            if "error" in tool_response_line:
                raise RuntimeError(
                    f"MCP tool error: {tool_response_line['error']}"
                )

            return tool_response_line.get("result", {})

        except subprocess.TimeoutExpired:
            process.kill()
            raise TimeoutError("MCP server timeout")
        except Exception as e:
            raise RuntimeError(f"MCP call failed: {e}")

    def listen(
        self,
        timeout_ms: int = 30000,
        silence_timeout_ms: int = 2000,
        auto_stop: bool = True
    ) -> str:
        """
        Record audio from microphone and transcribe.

        Args:
            timeout_ms: Maximum recording duration in milliseconds (default: 30s)
            silence_timeout_ms: Stop after this much silence in ms (default: 2s)
            auto_stop: Automatically stop on silence (default: True)

        Returns:
            Transcribed text
        """
        print(f"\n🎤 Listening... (max {timeout_ms/1000}s, silence timeout {silence_timeout_ms/1000}s)")
        print("   Speak your flight requirement now!")

        arguments = {
            "timeout_ms": timeout_ms,
            "silence_timeout_ms": silence_timeout_ms,
            "auto_stop": auto_stop
        }

        try:
            result = self._call_mcp_tool("listen", arguments)

            # Extract transcription from result
            if isinstance(result, dict):
                text = result.get("content", [{}])[0].get("text", "")
            else:
                text = str(result)

            if text:
                print(f"✓ Transcribed: '{text}'")
                return text
            else:
                print("⚠️  No speech detected")
                return ""

        except Exception as e:
            print(f"❌ Recording failed: {e}")
            return ""

    def transcribe_file(self, file_path: str) -> str:
        """
        Transcribe an existing audio file.

        Args:
            file_path: Path to WAV audio file

        Returns:
            Transcribed text
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        print(f"\n🔄 Transcribing file: {file_path}")

        arguments = {"file_path": file_path}

        try:
            result = self._call_mcp_tool("transcribe_file", arguments)

            # Extract transcription from result
            if isinstance(result, dict):
                text = result.get("content", [{}])[0].get("text", "")
            else:
                text = str(result)

            if text:
                print(f"✓ Transcribed: '{text}'")
                return text
            else:
                print("⚠️  No text found in audio")
                return ""

        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return ""


def main():
    """Test the MCP client"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Voice-to-Text MCP Client for Flight Search"
    )

    parser.add_argument(
        "--mcp-server",
        type=str,
        default="voice-to-text-mcp/target/release/voice-to-text-mcp",
        help="Path to MCP server binary"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="voice-to-text-mcp/models/ggml-base.en.bin",
        help="Path to Whisper model"
    )

    parser.add_argument(
        "--listen",
        action="store_true",
        help="Record and transcribe voice"
    )

    parser.add_argument(
        "--transcribe",
        type=str,
        help="Transcribe an audio file"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Recording timeout in milliseconds"
    )

    parser.add_argument(
        "--silence-timeout",
        type=int,
        default=2000,
        help="Silence timeout in milliseconds"
    )

    args = parser.parse_args()

    try:
        # Initialize client
        client = VoiceToTextMCPClient(args.mcp_server, args.model)

        if args.listen:
            # Record and transcribe
            text = client.listen(
                timeout_ms=args.timeout,
                silence_timeout_ms=args.silence_timeout
            )

            if text:
                print("\n" + "=" * 60)
                print("📝 TRANSCRIPTION:")
                print("=" * 60)
                print(text)
                print("=" * 60)
                print("\nℹ️  Use this with flight_search.py:")
                print(f'   python3 flight_search.py --query "{text}"')

        elif args.transcribe:
            # Transcribe file
            text = client.transcribe_file(args.transcribe)

            if text:
                print("\n" + "=" * 60)
                print("📝 TRANSCRIPTION:")
                print("=" * 60)
                print(text)
                print("=" * 60)

        else:
            parser.print_help()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
