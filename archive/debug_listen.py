#!/usr/bin/env python3
"""Debug the listen tool call"""

import subprocess
import json
import sys
import time

mcp_server = "voice-to-text-mcp/target/release/voice-to-text-mcp"
model = "voice-to-text-mcp/models/ggml-base.en.bin"

print("Starting MCP server...")
process = subprocess.Popen(
    [mcp_server, "--mcp-server", model],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

try:
    # Initialize
    print("\n1. Initialize")
    init_req = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "debug", "version": "1.0"}}}
    process.stdin.write(json.dumps(init_req) + "\n")
    process.stdin.flush()
    print(f"Response: {process.stdout.readline().strip()}")

    # Initialized notification
    print("\n2. Initialized notification")
    process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
    process.stdin.flush()

    # Call listen (5 second timeout for testing)
    print("\n3. Calling listen tool (5s timeout, speak now!)")
    listen_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "listen",
            "arguments": {
                "timeout_ms": 5000,
                "silence_timeout_ms": 1000,
                "auto_stop": True
            }
        }
    }
    process.stdin.write(json.dumps(listen_req) + "\n")
    process.stdin.flush()
    print("Sent request, waiting for response...")
    print("SPEAK NOW!")

    # Wait for response (this will take ~5 seconds + processing)
    start = time.time()
    response_line = None
    while True:
        line = process.stdout.readline()
        elapsed = time.time() - start
        print(f"[{elapsed:.1f}s] Read line: {len(line) if line else 0} chars")

        if not line:
            print("No more output from server")
            break

        line = line.strip()
        if not line:
            continue

        try:
            response = json.loads(line)
            print(f"Parsed JSON: {json.dumps(response, indent=2)}")
            if response.get("id") == 1:
                response_line = response
                break
        except json.JSONDecodeError as e:
            print(f"Not JSON: {line[:100]}")

    if response_line:
        print("\n✅ Got response!")
        print(json.dumps(response_line, indent=2))

        # Extract text
        result = response_line.get("result", {})
        content = result.get("content", [])
        if content:
            text = content[0].get("text", "")
            print(f"\n📝 Transcribed: {text}")
    else:
        print("\n❌ No response received")

    # Close stdin to signal we're done
    process.stdin.close()

    # Show stderr (non-blocking with timeout)
    print("\n📋 Stderr output (first 10 lines):")
    try:
        stderr_lines = []
        import select
        import os

        # Make stderr non-blocking
        stderr_fd = process.stderr.fileno()
        fl = os.get_blocking(stderr_fd)
        os.set_blocking(stderr_fd, False)

        # Try to read what's available
        try:
            stderr_data = process.stderr.read()
            if stderr_data:
                stderr_lines = stderr_data.split('\n')[:10]
        except:
            pass

        os.set_blocking(stderr_fd, fl)

        for line in stderr_lines:
            if line.strip():
                print(f"  {line}")
    except Exception as e:
        print(f"  (Could not read stderr: {e})")

finally:
    try:
        process.terminate()
        process.wait(timeout=2)
    except:
        process.kill()
        process.wait()
