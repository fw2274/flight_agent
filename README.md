# Flight Search Agent with MCP Server

This project demonstrates how to use the Flight Search MCP server from [flights.fctolabs.com](https://flights.fctolabs.com/) in VS Code.

## 🚀 Quick Start

### 1. Set Up Your Environment

First, make sure you have your virtual environment activated and your Google API key set:

```bash
# Activate virtual environment
source .venv/bin/activate

# Set your Google API key (get one from https://aistudio.google.com/app/api-keys)
export GOOGLE_API_KEY='your-api-key-here'
```

### 2. Run the Flight Search Agent

```bash
python flight_search_mcp.py
```

## 📝 What's Configured

### VS Code Settings

The MCP server has been added to your VS Code settings at:
- **Global**: `~/Library/Application Support/Code/User/settings.json`
- **Workspace**: `.vscode/settings.json`

Configuration:
```json
{
  "claude.mcpServers": {
    "flight-search": {
      "command": "npx",
      "args": ["mcp-remote", "https://flights.fctolabs.com/mcp"]
    }
  }
}
```

### What the MCP Server Provides

The Flight Search MCP server gives you access to:
- 🔍 **Flight Search**: Find cheapest flights, nonstop routes, and price ranges
- 📅 **Calendar Search**: Identify optimal prices across months or weeks
- 🌍 **Travel Database**: Access airports, cities, airlines, and country info
- 🔗 **Booking Integration**: Get direct booking links
- 🗺️ **Discovery Tools**: Find popular routes and alternatives

## 🎯 Example Queries

Try these example queries in the script:

1. **Simple search**:
   ```
   "Find me flights from San Francisco to New York next week"
   ```

2. **Cheapest flights**:
   ```
   "What are the cheapest flights from Los Angeles to London in December?"
   ```

3. **Nonstop flights**:
   ```
   "Find nonstop flights from Chicago to Tokyo"
   ```

4. **Calendar search**:
   ```
   "Show me flight prices from Seattle to Paris for January"
   ```

## 🔧 Using in VS Code with Claude Code Extension

If you're using the Claude Code extension:

1. **Reload VS Code**: Press `Cmd+Shift+P` → "Developer: Reload Window"
2. **Start chatting**: The flight-search MCP server will be available in Claude Code
3. **Ask about flights**: Just ask naturally, like "Find flights from NYC to SF"

## 📚 Files in This Project

- `flight_search_mcp.py` - Python script to use the MCP server programmatically
- `day-1a-from-prompt-to-action.ipynb` - Kaggle AI Agents course notebook
- `day-1b-agent-architectures.ipynb` - Agent architectures course notebook
- `.vscode/settings.json` - VS Code workspace MCP configuration

## 🛠️ Requirements

All dependencies are already installed in `.venv`:
- `google-adk` - Agent Development Kit
- `jupyter` - For running notebooks
- Node.js/npx - For running the MCP remote server (usually pre-installed on macOS)

## 💡 Tips

- The MCP server runs remotely, so no local installation is needed
- Make sure you have a stable internet connection
- The server may take a few seconds to respond on first request
- Check the console for detailed logs and debugging info

## 🆘 Troubleshooting

**Issue**: `GOOGLE_API_KEY not set`
- **Solution**: Run `export GOOGLE_API_KEY='your-key'` in your terminal

**Issue**: MCP server not responding
- **Solution**: Check your internet connection and try again

**Issue**: `npx not found`
- **Solution**: Install Node.js from [nodejs.org](https://nodejs.org)

## 📖 Learn More

- [MCP Protocol](https://modelcontextprotocol.io/)
- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Flight Search MCP Server](https://flights.fctolabs.com/)
