"""
Test script to check if the Flight Search MCP server is accessible and working.

This script will:
1. Try to connect to the MCP server
2. List available tools
3. Verify the connection is working

Run: python test_mcp_connection.py
"""

import asyncio
import sys
from google.adk.tools.mcp_tool import McpToolset
from mcp import StdioServerParameters


async def test_mcp_connection():
    """Test connection to the Flight Search MCP server"""

    print("\n" + "=" * 60)
    print("🔍 Testing Flight Search MCP Server Connection")
    print("=" * 60 + "\n")

    print("📡 Attempting to connect to: https://flights.fctolabs.com/mcp")
    print("   Using: npx mcp-remote\n")

    try:
        # Create MCP toolset
        print("⏳ Creating MCP toolset...")
        flight_tools = McpToolset(
            connection_params=StdioServerParameters(
                command="npx",
                args=["mcp-remote", "https://flights.fctolabs.com/mcp"]
            )
        )
        print("✅ MCP toolset created successfully\n")

        # Try to get the list of available tools
        print("⏳ Fetching available tools from the server...")
        tools = await flight_tools.get_tools()

        if tools:
            print(f"✅ SUCCESS! Connected to MCP server\n")
            print(f"📋 Found {len(tools)} available tools:\n")

            for i, tool in enumerate(tools, 1):
                print(f"   {i}. {tool.name}")
                if hasattr(tool, 'description') and tool.description:
                    # Indent and wrap description
                    desc = tool.description.strip().replace('\n', ' ')
                    if len(desc) > 70:
                        desc = desc[:67] + "..."
                    print(f"      {desc}")
                print()

            print("=" * 60)
            print("✅ MCP Server is ONLINE and WORKING!")
            print("=" * 60 + "\n")

            return True

        else:
            print("⚠️  Server connected but returned no tools")
            return False

    except ConnectionError as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print("\n💡 Possible reasons:")
        print("   - The MCP server might be down")
        print("   - Network connectivity issues")
        print("   - The server URL might have changed")
        return False

    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        print("\n💡 Make sure you have installed all dependencies:")
        print("   pip install google-adk mcp")
        return False

    except FileNotFoundError as e:
        print(f"❌ NPX NOT FOUND: {e}")
        print("\n💡 You need Node.js/npx installed:")
        print("   - macOS: brew install node")
        print("   - Or download from: https://nodejs.org/")
        return False

    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        print("\n💡 Try running with verbose output:")
        print("   python -u test_mcp_connection.py")
        return False

    finally:
        # Clean up the connection
        try:
            await flight_tools.close()
            print("🔌 Connection closed gracefully\n")
        except:
            pass


async def quick_health_check():
    """Quick check if npx and network are available"""
    import subprocess

    print("🏥 Running pre-flight checks...\n")

    # Check if npx is available
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"✅ npx is installed (version: {result.stdout.strip()})")
        else:
            print("⚠️  npx found but returned an error")
            return False
    except FileNotFoundError:
        print("❌ npx not found - please install Node.js")
        return False
    except Exception as e:
        print(f"⚠️  Error checking npx: {e}")
        return False

    # Check if mcp-remote package is accessible
    print("✅ Node.js/npx is ready")

    # Check network connectivity to the domain
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "https://flights.fctolabs.com/"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.stdout.strip() == "200":
            print("✅ Network connectivity to flights.fctolabs.com confirmed")
        else:
            print(f"⚠️  Website returned status code: {result.stdout.strip()}")
    except Exception as e:
        print(f"⚠️  Could not verify network connectivity: {e}")

    print()
    return True


if __name__ == "__main__":
    async def main():
        # Run health checks first
        health_ok = await quick_health_check()

        if not health_ok:
            print("\n❌ Pre-flight checks failed")
            print("Please resolve the issues above before testing MCP connection\n")
            sys.exit(1)

        # Test the MCP connection
        success = await test_mcp_connection()

        if success:
            print("🎉 You're all set! The MCP server is ready to use.")
            print("   Run: python flight_search_mcp.py\n")
            sys.exit(0)
        else:
            print("❌ MCP server connection test failed\n")
            sys.exit(1)

    asyncio.run(main())
