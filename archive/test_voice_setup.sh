#!/bin/bash
# Test script to verify voice-to-text MCP integration setup

echo "=========================================="
echo "Voice-to-Text MCP Setup Verification"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Rust installation
echo "1. Checking Rust installation..."
if command -v cargo &> /dev/null; then
    CARGO_VERSION=$(cargo --version)
    echo -e "${GREEN}✓${NC} Rust installed: $CARGO_VERSION"
else
    echo -e "${RED}✗${NC} Rust not installed"
    echo "   Install: https://rustup.rs/"
    exit 1
fi
echo ""

# Check 2: MCP repository
echo "2. Checking voice-to-text-mcp repository..."
if [ -d "voice-to-text-mcp" ]; then
    echo -e "${GREEN}✓${NC} Repository cloned"
else
    echo -e "${RED}✗${NC} Repository not found"
    echo "   Clone: git clone https://github.com/acazau/voice-to-text-mcp.git"
    exit 1
fi
echo ""

# Check 3: MCP server binary
echo "3. Checking MCP server binary..."
MCP_BINARY="voice-to-text-mcp/target/release/voice-to-text-mcp"
if [ -f "$MCP_BINARY" ]; then
    echo -e "${GREEN}✓${NC} MCP server built"
    ls -lh "$MCP_BINARY"
else
    echo -e "${YELLOW}⚠${NC} MCP server not built"
    echo "   Building now..."
    cd voice-to-text-mcp
    cargo build --release
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} Build successful"
        cd ..
    else
        echo -e "${RED}✗${NC} Build failed"
        exit 1
    fi
fi
echo ""

# Check 4: Whisper model
echo "4. Checking Whisper model..."
MODEL_PATH="voice-to-text-mcp/models/ggml-base.en.bin"
if [ -f "$MODEL_PATH" ]; then
    echo -e "${GREEN}✓${NC} Model downloaded: ggml-base.en.bin"
    ls -lh "$MODEL_PATH"
else
    echo -e "${YELLOW}⚠${NC} Model not found"
    echo "   Download: cd voice-to-text-mcp && ./scripts/download-models.sh"
    # Check for alternative models
    if ls voice-to-text-mcp/models/*.bin 1> /dev/null 2>&1; then
        echo "   Available models:"
        ls -lh voice-to-text-mcp/models/*.bin
    fi
fi
echo ""

# Check 5: Python files
echo "5. Checking Python integration files..."
if [ -f "voice_mcp_client.py" ]; then
    echo -e "${GREEN}✓${NC} voice_mcp_client.py present"
else
    echo -e "${RED}✗${NC} voice_mcp_client.py missing"
    exit 1
fi

if [ -f "flight_search_vtt.py" ]; then
    echo -e "${GREEN}✓${NC} flight_search_vtt.py present"
else
    echo -e "${RED}✗${NC} flight_search_vtt.py missing"
    exit 1
fi
echo ""

# Check 6: Environment variables
echo "6. Checking environment variables..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"

    # Check for required keys (without showing values)
    if grep -q "GOOGLE_API_KEY" .env; then
        echo -e "${GREEN}✓${NC} GOOGLE_API_KEY configured"
    else
        echo -e "${YELLOW}⚠${NC} GOOGLE_API_KEY not set"
    fi

    if grep -q "AMADEUS_API_KEY" .env; then
        echo -e "${GREEN}✓${NC} AMADEUS_API_KEY configured"
    else
        echo -e "${YELLOW}⚠${NC} AMADEUS_API_KEY not set"
    fi

    if grep -q "AMADEUS_API_SECRET" .env; then
        echo -e "${GREEN}✓${NC} AMADEUS_API_SECRET configured"
    else
        echo -e "${YELLOW}⚠${NC} AMADEUS_API_SECRET not set"
    fi
else
    echo -e "${RED}✗${NC} .env file not found"
fi
echo ""

# Check 7: Python dependencies
echo "7. Checking Python dependencies..."
python3 -c "import google.adk" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} google.adk installed"
else
    echo -e "${YELLOW}⚠${NC} google.adk not installed"
fi

python3 -c "from dotenv import load_dotenv" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} python-dotenv installed"
else
    echo -e "${YELLOW}⚠${NC} python-dotenv not installed"
fi
echo ""

# Summary
echo "=========================================="
echo "Setup Summary"
echo "=========================================="
echo ""

if [ -f "$MCP_BINARY" ] && [ -f "$MODEL_PATH" ]; then
    echo -e "${GREEN}✓ Voice-to-Text MCP is ready!${NC}"
    echo ""
    echo "Quick start commands:"
    echo ""
    echo "  # Test voice input (records for up to 30s)"
    echo "  python3 flight_search_vtt.py --voice"
    echo ""
    echo "  # Test with text input"
    echo "  python3 flight_search_vtt.py --query \"Find flights from LAX to NYC\""
    echo ""
    echo "  # Test MCP client directly"
    echo "  python3 voice_mcp_client.py --listen"
    echo ""
else
    echo -e "${YELLOW}⚠ Setup incomplete${NC}"
    echo ""
    echo "Next steps:"
    if [ ! -f "$MCP_BINARY" ]; then
        echo "  1. Build MCP server: cd voice-to-text-mcp && cargo build --release"
    fi
    if [ ! -f "$MODEL_PATH" ]; then
        echo "  2. Download model: cd voice-to-text-mcp && ./scripts/download-models.sh"
    fi
    echo ""
    echo "See VOICE_SETUP.md for detailed instructions"
fi
echo ""
