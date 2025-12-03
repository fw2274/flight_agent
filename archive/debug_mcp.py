#!/usr/bin/env python3
"""Debug MCP protocol interaction"""

import subprocess
import json
import sys

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
    # Step 1: Initialize
    print("\n1. Sending initialize request...")
    init_req = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "debug-client", "version": "1.0"}
        }
    }
    print(f"Request: {json.dumps(init_req)}")
    process.stdin.write(json.dumps(init_req) + "\n")
    process.stdin.flush()

    response = process.stdout.readline()
    print(f"Response: {response.strip()}")

    # Step 2: Initialized notification
    print("\n2. Sending initialized notification...")
    init_notif = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }
    print(f"Notification: {json.dumps(init_notif)}")
    process.stdin.write(json.dumps(init_notif) + "\n")
    process.stdin.flush()

    # Step 3: List tools
    print("\n3. Requesting tools list...")
    list_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list"
    }
    print(f"Request: {json.dumps(list_req)}")
    process.stdin.write(json.dumps(list_req) + "\n")
    process.stdin.flush()

    response = process.stdout.readline()
    print(f"Response: {response.strip()}")

    # Parse and show tools
    try:
        tools_response = json.loads(response)
        if "result" in tools_response:
            print("\nAvailable tools:")
            for tool in tools_response["result"].get("tools", []):
                print(f"  - {tool.get('name')}: {tool.get('description', 'No description')}")
    except:
        pass

    print("\n4. Closing connection...")
    process.stdin.close()

    # Read any remaining output
    print("\nRemaining stdout:")
    for line in process.stdout:
        print(f"  {line.strip()}")

    print("\nStderr:")
    stderr = process.stderr.read()
    if stderr:
        print(stderr)

finally:
    process.terminate()
    process.wait()
