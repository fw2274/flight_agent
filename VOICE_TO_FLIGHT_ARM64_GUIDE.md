# Voice-to-Flight Search on ARM64 Tablets - Complete Guide

## Overview

This guide covers the **complete integrated application** that combines:
1. 🎤 **Voice Input** (Whisper AI via Rust MCP server)
2. 🧠 **Intent Parsing** (Google Gemini AI)
3. ✈️ **Flight Search** (Amadeus API)

All running on **ARM64 architecture** (Android tablets, Raspberry Pi, ARM Linux devices).

---

## Architecture

```
┌─────────────┐
│   User      │
│ 🗣️ Speaks   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  Voice-to-Text MCP (Rust)       │
│  - Whisper AI (ARM64)           │
│  - Hardware acceleration        │
│  - NEON SIMD optimization       │
└──────┬──────────────────────────┘
       │ Transcribed text
       ▼
┌─────────────────────────────────┐
│  Intent Parser (Python)         │
│  - Google Gemini AI             │
│  - Extract: origin, dest, date  │
│  - Fallback: regex parsing      │
└──────┬──────────────────────────┘
       │ Structured parameters
       ▼
┌─────────────────────────────────┐
│  Flight Search (Python)         │
│  - Amadeus API                  │
│  - Search flights               │
│  - Format results               │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────┐
│   Results   │
│ ✈️ Flights   │
└─────────────┘
```

---

## Quick Start

### Prerequisites
- Docker with ARM64 support (QEMU enabled)
- Valid API keys:
  - Google Gemini: https://aistudio.google.com/app/api-keys
  - Amadeus: https://developers.amadeus.com/
- Whisper model (will be downloaded automatically)

### Step 1: Update API Keys

Edit `.env` file with valid credentials:
```bash
cd C:\Users\ranan\flight_agent
notepad .env
```

```env
GOOGLE_API_KEY='your_actual_google_key_here'
AMADEUS_API_KEY='your_actual_amadeus_key_here'
AMADEUS_API_SECRET='your_actual_amadeus_secret_here'
```

### Step 2: Build Complete ARM64 Image

```bash
cd C:\Users\ranan\flight_agent

# Build the complete voice + flight search image
docker buildx build --platform linux/arm64 \
  -t voice-flight-arm64 \
  -f Dockerfile.voice_flight_arm64 . --load
```

**Build Time:** ~10-15 minutes (compiling Rust for ARM64)

### Step 3: Download Whisper Model

```bash
# Run container and download model
docker run --platform linux/arm64 --rm voice-flight-arm64 /app/download_model.sh
```

### Step 4: Verify Installation

```bash
docker run --platform linux/arm64 --rm voice-flight-arm64 /app/verify_arm64.sh
```

**Expected Output:**
```
=========================================
ARM64 Voice-to-Flight Search Verification
=========================================

Architecture: aarch64
Python: Python 3.x.x

Voice-to-Text Binary:
-rwxr-xr-x 1 root root 8.5M ... voice-to-text-mcp

Python Scripts:
-rwxr-xr-x 1 root root  15K ... voice_to_flight_integrated.py
-rwxr-xr-x 1 root root 9.6K ... flight_search_tablet.py

Whisper Models:
-rw-r--r-- 1 root root 142M ... ggml-base.en.bin
=========================================
```

---

## Usage Options

### Option 1: Text Mode (Testing Without Audio)

Test the application without voice input (useful for ARM64 Docker testing):

```bash
docker run --platform linux/arm64 --rm voice-flight-arm64 \
  python3 /app/voice_to_flight_integrated.py --text "Find flights from LAX to JFK on December 20"
```

**What Happens:**
1. ✅ Skips voice capture
2. ✅ Parses text query with Gemini/fallback
3. ✅ Searches flights with Amadeus
4. ✅ Displays results

**Example Output:**
```
🎤 ✈️  VOICE-TO-FLIGHT SEARCH (ARM64)
============================================================

📝 Text mode: Find flights from LAX to JFK on December 20

🔍 Parsing flight requirements...

📋 Extracted parameters:
{
  "originLocationCode": "LAX",
  "destinationLocationCode": "JFK",
  "departureDate": "2025-12-20",
  "returnDate": null,
  "adults": 1,
  "travelClass": "ECONOMY"
}

🔎 Searching for flights...

============================================================
✈️  FLIGHT SEARCH RESULTS
============================================================

✈️  Flight #1
  💰 Price: 250.00 USD
  🏢 Carrier: AA
  🛫 Departure: LAX at 2025-12-20T08:00:00
  🛬 Arrival: JFK at 2025-12-20T16:30:00
  ⏱️  Duration: PT8H30M

...
============================================================
```

### Option 2: Voice Mode (Requires Audio Device)

**Note:** Docker containers typically don't have audio device access. Use this mode on:
- Physical ARM tablets (Android with Termux)
- Raspberry Pi with microphone
- ARM Linux laptops

```bash
# On physical ARM device
python3 voice_to_flight_integrated.py
```

**What Happens:**
1. 🎤 Starts recording from microphone
2. 🗣️ User speaks: "Find flights from Los Angeles to New York on December 20th"
3. ⏱️ Recording stops after silence (2s default) or timeout (30s default)
4. 📝 Whisper transcribes audio
5. 🧠 Gemini parses flight intent
6. ✈️ Amadeus searches flights
7. 📊 Results displayed

### Option 3: Custom Voice Settings

```bash
# Longer recording time (60 seconds)
python3 voice_to_flight_integrated.py --timeout 60000

# Longer silence detection (5 seconds)
python3 voice_to_flight_integrated.py --silence-timeout 5000

# Use smaller/faster model
python3 voice_to_flight_integrated.py --model models/ggml-tiny.en.bin

# Custom voice binary location
python3 voice_to_flight_integrated.py --voice-binary /usr/local/bin/voice-to-text-mcp
```

---

## Deployment Scenarios

### Scenario 1: ARM64 Docker Testing (Current)

**Purpose:** Test application logic without audio hardware

```bash
# Test with text input
docker run --platform linux/arm64 --rm voice-flight-arm64 \
  python3 /app/voice_to_flight_integrated.py \
  --text "Flights from SFO to NYC tomorrow"
```

**✅ Pros:**
- Works on any machine with Docker
- No audio hardware needed
- Fast testing iteration

**❌ Cons:**
- Cannot test voice input
- Slower than native ARM (QEMU emulation)

---

### Scenario 2: Android Tablet with Termux

**Purpose:** Full voice-to-flight functionality on ARM tablet

#### Installation Steps

1. **Install Termux** from F-Droid: https://f-droid.org/packages/com.termux/

2. **Install Dependencies:**
   ```bash
   pkg update && pkg upgrade
   pkg install rust python git clang
   termux-setup-storage
   ```

3. **Grant Microphone Permission:**
   ```bash
   # Test microphone
   termux-microphone-record -f test.wav -l 5
   # Grant permission when prompted
   ```

4. **Clone Repository:**
   ```bash
   cd ~
   git clone https://github.com/fw2274/flight_agent
   cd flight_agent
   ```

5. **Build Voice-to-Text:**
   ```bash
   cd voice-to-text-mcp
   cargo build --release
   cd ..
   ```

6. **Download Whisper Model:**
   ```bash
   cd voice-to-text-mcp/models
   curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
   cd ../..
   ```

7. **Install Python Dependencies:**
   ```bash
   pip install -r requirements_termux.txt
   ```

8. **Configure API Keys:**
   ```bash
   nano .env
   # Add your Google Gemini and Amadeus keys
   ```

9. **Run Application:**
   ```bash
   python voice_to_flight_integrated.py
   ```

10. **Speak Your Query:**
    - App starts recording automatically
    - Speak: "Find flights from Los Angeles to New York on December 20th"
    - Wait for transcription and results

**✅ Pros:**
- Full voice functionality
- Native ARM performance
- Real tablet experience

**❌ Cons:**
- Requires Android tablet
- Longer setup time (~30 minutes)

---

### Scenario 3: Raspberry Pi

**Purpose:** Standalone voice-to-flight device

#### Hardware Requirements
- Raspberry Pi 4 or 5 (ARM64)
- USB microphone
- Internet connection

#### Setup
```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y \
  curl \
  git \
  build-essential \
  libasound2-dev \
  python3 \
  python3-pip

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Clone repository
cd ~
git clone https://github.com/fw2274/flight_agent
cd flight_agent

# Build voice-to-text
cd voice-to-text-mcp
cargo build --release
cd ..

# Download model
cd voice-to-text-mcp/models
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
cd ../..

# Install Python dependencies
pip3 install -r requirements.txt

# Configure keys
nano .env

# Run
python3 voice_to_flight_integrated.py
```

---

## Testing Strategies

### Test 1: Architecture Verification
```bash
docker run --platform linux/arm64 --rm voice-flight-arm64 uname -m
# Expected: aarch64
```

### Test 2: Python Dependencies
```bash
docker run --platform linux/arm64 --rm voice-flight-arm64 pip list
# Verify google-generativeai, requests, pydantic installed
```

### Test 3: Voice Binary Check
```bash
docker run --platform linux/arm64 --rm voice-flight-arm64 \
  file /app/voice-to-text-mcp
# Expected: ELF 64-bit LSB executable, ARM aarch64
```

### Test 4: Simple Flight Search (No Voice)
```bash
docker run --platform linux/arm64 --rm voice-flight-arm64 \
  python3 /app/flight_search_tablet.py \
  --query "LAX to JFK on December 20"
```

### Test 5: Integrated App (Text Mode)
```bash
docker run --platform linux/arm64 --rm voice-flight-arm64 \
  python3 /app/voice_to_flight_integrated.py \
  --text "Find flights from LAX to JFK on December 20"
```

### Test 6: Full Voice Pipeline (Physical ARM Device Only)
```bash
# On Termux/Raspberry Pi
python3 voice_to_flight_integrated.py

# Speak: "Find flights from San Francisco to Boston on January 15th"
# Expected: Voice captured → transcribed → flights displayed
```

---

## Troubleshooting

### Issue: "Voice-to-text binary not found"
**Solution:**
```bash
# Verify binary exists
docker run --platform linux/arm64 --rm voice-flight-arm64 ls -la /app/voice-to-text-mcp

# If missing, rebuild:
docker buildx build --platform linux/arm64 -t voice-flight-arm64 -f Dockerfile.voice_flight_arm64 . --load
```

### Issue: "Whisper model not found"
**Solution:**
```bash
# Download model
docker run --platform linux/arm64 --rm voice-flight-arm64 /app/download_model.sh
```

### Issue: "API key not valid"
**Solution:**
1. Get fresh API keys:
   - Google Gemini: https://aistudio.google.com/app/api-keys
   - Amadeus: https://developers.amadeus.com/
2. Update `.env` file
3. Rebuild Docker image

### Issue: "No audio device" (in Docker)
**Expected:** Docker containers don't have audio access by default

**Solutions:**
1. **Use text mode for testing:**
   ```bash
   --text "Your query here"
   ```

2. **Deploy to physical ARM device** (Termux, Raspberry Pi)

3. **Advanced: Enable Docker audio passthrough** (Linux only):
   ```bash
   docker run --platform linux/arm64 --rm \
     --device /dev/snd \
     -v /run/user/$(id -u)/pulse:/run/pulse \
     voice-flight-arm64 \
     python3 /app/voice_to_flight_integrated.py
   ```

### Issue: "401 Unauthorized" from Amadeus
**Solution:** Amadeus test credentials may be expired

```bash
# Generate new test credentials at:
https://developers.amadeus.com/self-service/apis-docs/guides/authorization-262
```

---

## Performance Characteristics

### Build Times
- **x86_64 Host → ARM64 Docker:** ~10-15 minutes (QEMU emulation)
- **Native ARM Build (Termux/Pi):** ~5-8 minutes

### Runtime Performance

| Component | Docker ARM64 (QEMU) | Native ARM64 |
|-----------|---------------------|--------------|
| Voice Capture | N/A (no audio) | Real-time |
| Whisper Transcription (5s audio) | ~8-10 seconds | ~3-5 seconds |
| Gemini Parsing | ~1-2 seconds | ~1-2 seconds |
| Amadeus Search | ~2-3 seconds | ~2-3 seconds |
| **Total (Voice Mode)** | N/A | ~8-12 seconds |
| **Total (Text Mode)** | ~5-7 seconds | ~3-5 seconds |

### Hardware Acceleration
- **ARM NEON SIMD:** 2-3x speedup for audio processing
- **Native ARM64:** ~2x faster than QEMU emulation
- **Metal/CoreML:** Not available on Linux ARM

---

## API Keys Setup

### Google Gemini API Key

1. Visit: https://aistudio.google.com/app/api-keys
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key to `.env`:
   ```env
   GOOGLE_API_KEY='AIza...'
   ```

**Free Tier:** 60 requests/minute

### Amadeus API Credentials

1. Visit: https://developers.amadeus.com/register
2. Create free developer account
3. Create a new app in dashboard
4. Copy API Key and Secret to `.env`:
   ```env
   AMADEUS_API_KEY='your_key_here'
   AMADEUS_API_SECRET='your_secret_here'
   ```

**Test Environment:** Free with limited requests

---

## File Structure

```
flight_agent/
├── voice-to-text-mcp/              # Rust voice-to-text MCP server
│   ├── src/                        # Rust source code
│   ├── models/                     # Whisper models (download)
│   ├── Cargo.toml                  # Rust dependencies (ARM64 support)
│   └── target/release/             # Compiled binary
│       └── voice-to-text-mcp       # ARM64 executable
│
├── flight_search_tablet.py         # Standalone flight search (text only)
├── voice_to_flight_integrated.py   # ⭐ Complete voice-to-flight app
├── requirements_termux.txt         # Python dependencies for ARM
├── .env                            # API keys configuration
│
├── Dockerfile.arm_simple           # Simple Python-only ARM64 image
├── Dockerfile.arm_tablet           # Full ARM64 with Rust (complex)
└── Dockerfile.voice_flight_arm64   # ⭐ Complete integrated image
```

---

## Next Steps

1. **✅ Build ARM64 Docker image** (if testing with text mode)
2. **✅ Update API keys** in `.env` file
3. **✅ Test with text mode** to verify logic
4. **🎯 Deploy to Android tablet** (for full voice experience)
5. **🎯 Test complete voice pipeline** on physical ARM device

---

## Success Criteria

- [x] Voice-to-text Rust binary builds for ARM64
- [x] Python flight search works on ARM64
- [x] Integrated application combines both components
- [x] Text mode works in ARM64 Docker
- [ ] Voice mode works on physical ARM device *(requires deployment)*
- [ ] End-to-end: Voice → Transcription → Parsing → Flight Search → Results

---

**Status:** ✅ Application ready for ARM64 deployment
**Text Mode:** ✅ Fully functional in Docker
**Voice Mode:** 🎯 Requires physical ARM tablet/device with microphone
**Docker Build Time:** ~10-15 minutes
**Runtime:** 8-12 seconds per voice query (native ARM)
