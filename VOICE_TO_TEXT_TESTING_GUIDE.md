# Voice-to-Text Agent Testing Guide

## Overview

The voice-to-text agent is a **Rust-based MCP server** using OpenAI's Whisper AI for speech-to-text transcription. It supports:
- Hardware acceleration (Metal/CoreML on macOS, CUDA on Linux/Windows)
- Real-time audio capture from microphone
- File-based transcription of existing audio
- MCP protocol integration with Claude Code

## Testing Options

### Option 1: Testing on Your Windows Machine (x86_64)

This is the **easiest option** for testing the voice-to-text capabilities.

#### Prerequisites
```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# On Windows, download from: https://rustup.rs/
```

#### Build the Voice-to-Text Server
```bash
cd C:\Users\ranan\flight_agent\voice-to-text-mcp

# Build the Rust binary
cargo build --release

# This will take 2-6 minutes on first build
# Subsequent builds are faster
```

#### Download a Whisper Model
```bash
# Use the interactive script (Linux/macOS)
./scripts/download-models.sh

# Or manually download (Windows)
cd models
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
cd ..
```

**Model Recommendations:**
| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| `ggml-tiny.en.bin` | 75MB | Fastest | Quick testing |
| `ggml-base.en.bin` | 142MB | Fast | ⭐ **Recommended** - Best balance |
| `ggml-small.en.bin` | 466MB | Slower | High accuracy |

#### Test Voice Recording
```bash
cd C:\Users\ranan\flight_agent\voice-to-text-mcp

# Test 1: Simple 10-second recording
./target/release/voice-to-text-mcp --timeout-ms 10000 models/ggml-base.en.bin

# Test 2: With debug mode (saves audio file)
./target/release/voice-to-text-mcp --debug --timeout-ms 10000 models/ggml-base.en.bin

# Test 3: With custom silence detection
./target/release/voice-to-text-mcp --timeout-ms 30000 --silence-timeout-ms 2000 models/ggml-base.en.bin

# Test 4: No auto-stop (records for full duration)
./target/release/voice-to-text-mcp --no-auto-stop --timeout-ms 5000 models/ggml-base.en.bin
```

**What Happens:**
1. Program starts and immediately begins recording from your microphone
2. Speak something (e.g., "Testing voice to text functionality")
3. Recording stops after silence or timeout
4. Whisper transcribes the audio
5. Transcription is printed to console

**Example Output:**
```
Recording started. Speak now...
Recording stopped after 5.2 seconds
Transcribing audio...
Transcription: "Testing voice to text functionality"
```

#### Test File Transcription

If you have existing audio files:
```bash
# Test with debug audio file (after recording with --debug)
./target/release/voice-to-text-mcp --transcribe-file debug/audio_20250203_123045_raw.wav models/ggml-base.en.bin
```

---

### Option 2: Testing on ARM64 Docker (Limited)

Testing voice-to-text in ARM64 Docker is **challenging** because:
- Docker containers typically don't have audio device access
- Requires special configuration for audio passthrough
- Better for testing the build process than actual functionality

#### Build for ARM64
```bash
cd C:\Users\ranan\flight_agent

# Create Dockerfile for voice-to-text ARM64
cat > Dockerfile.voice_arm64 << 'EOF'
FROM rust:1.70 AS builder
WORKDIR /build

# Install ARM64 dependencies
RUN apt-get update && apt-get install -y \
    libasound2-dev \
    pkg-config \
    curl

# Copy voice-to-text source
COPY voice-to-text-mcp/ /build/

# Build for ARM64
RUN cargo build --release

# Runtime image
FROM arm64v8/ubuntu:22.04
RUN apt-get update && apt-get install -y libasound2
WORKDIR /app
COPY --from=builder /build/target/release/voice-to-text-mcp /app/
COPY --from=builder /build/models/ /app/models/

CMD ["/bin/bash"]
EOF

# Build the ARM64 container
docker buildx build --platform linux/arm64 -t voice-to-text-arm64 -f Dockerfile.voice_arm64 . --load
```

**Note:** This proves the Rust code compiles for ARM64, but you won't be able to test audio recording without audio device passthrough.

---

### Option 3: Testing on Android Tablet with Termux (Most Realistic)

This is the **best option** for testing ARM tablet voice capabilities.

#### Step 1: Install Termux on Android Tablet

1. Download Termux from F-Droid: https://f-droid.org/packages/com.termux/
2. Open Termux and update packages:
   ```bash
   pkg update && pkg upgrade
   ```

#### Step 2: Install Dependencies
```bash
# Install Rust
pkg install rust

# Install audio dependencies
pkg install libasound-dev

# Install git
pkg install git
```

#### Step 3: Grant Microphone Permissions
```bash
# Request microphone permission
termux-microphone-record -f test.wav -l 5

# This will prompt for permission
# Grant "Allow" when prompted
```

#### Step 4: Clone and Build
```bash
# Clone the repository
cd ~
git clone https://github.com/fw2274/flight_agent
cd flight_agent/voice-to-text-mcp

# Build for ARM (will take 10-15 minutes on tablet)
cargo build --release
```

#### Step 5: Download Model
```bash
cd models
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
cd ..
```

#### Step 6: Test Voice Recording
```bash
# Test recording
./target/release/voice-to-text-mcp --timeout-ms 10000 models/ggml-base.en.bin
```

**Expected Behavior:**
- Termux will use the tablet's microphone
- Speak into the tablet
- Whisper transcribes your speech
- Results displayed in Termux terminal

---

### Option 4: Testing with MCP Integration (Claude Code)

If you have Claude Code installed:

#### Step 1: Build and Install
```bash
cd C:\Users\ranan\flight_agent\voice-to-text-mcp
cargo build --release

# Download model
cd models
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
cd ..

# Add to Claude Code
claude mcp add --scope project voice-to-text -- \
  ./target/release/voice-to-text-mcp --mcp-server models/ggml-base.en.bin
```

#### Step 2: Use in Claude Code
```bash
# In Claude Code, use the /listen command
/listen

# With custom timeout
/listen timeout_ms=30000

# With longer silence detection
/listen timeout_ms=60000 silence_timeout_ms=3000
```

---

## Troubleshooting

### Issue: "No input device available"
**Solution:**
- **Windows**: Check microphone permissions in Windows Settings
- **Linux**: Install ALSA: `sudo apt-get install libasound2-dev`
- **Android Termux**: Grant microphone permissions: `termux-microphone-record -h`

### Issue: "Model file not found"
**Solution:**
```bash
# Download the model
cd models
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
```

### Issue: Build fails with "whisper-rs compilation error"
**Solution:**
- Ensure you have latest Rust: `rustup update`
- On Linux: Install CUDA toolkit (optional, for GPU acceleration)
- On Windows: Install Visual Studio Build Tools

### Issue: Poor transcription quality
**Solutions:**
- Use a better model: `ggml-small.en.bin` or `ggml-medium.en.bin`
- Ensure microphone quality is good
- Reduce background noise
- Speak clearly and at moderate pace

### Issue: Transcription is slow
**Solutions:**
- Use smaller model: `ggml-tiny.en.bin`
- Enable hardware acceleration (GPU/CoreML)
- On macOS: First CoreML run takes 15-20 minutes (compiling model), then it's cached

---

## Testing Scenarios

### Scenario 1: Quick Functionality Test
```bash
# 5-second test with tiny model
./target/release/voice-to-text-mcp --timeout-ms 5000 models/ggml-tiny.en.bin
```
**Say:** "Testing one two three"
**Expected:** "Testing one two three"

### Scenario 2: Flight Search Voice Command
```bash
# 15-second test with base model
./target/release/voice-to-text-mcp --timeout-ms 15000 models/ggml-base.en.bin
```
**Say:** "Find flights from Los Angeles to New York on December 20th"
**Expected:** "Find flights from Los Angeles to New York on December 20th"

### Scenario 3: Debug Audio Issues
```bash
# Record with debug mode
./target/release/voice-to-text-mcp --debug --timeout-ms 10000 models/ggml-base.en.bin
```
**Result:** Audio saved to `debug/audio_YYYYMMDD_HHMMSS_raw.wav`
**Action:** Listen to the WAV file to verify audio capture is working

### Scenario 4: Transcribe Existing Audio
```bash
# Transcribe a previously saved audio file
./target/release/voice-to-text-mcp --transcribe-file debug/audio_20250203_123045_raw.wav models/ggml-base.en.bin
```

---

## Performance Benchmarks

### Recording Speed
- **Audio Capture**: Real-time (no delay)
- **Transcription**:
  - `ggml-tiny.en`: ~5 seconds of audio transcribed in 1 second
  - `ggml-base.en`: ~5 seconds of audio transcribed in 2 seconds
  - `ggml-small.en`: ~5 seconds of audio transcribed in 4 seconds

### Hardware Acceleration
- **CPU Only**: Baseline speed
- **CUDA (NVIDIA GPU)**: 2-4x faster
- **Metal (Mac)**: 1.5-2x faster
- **CoreML (Apple Silicon)**: 3x+ faster (after initial 15-20min compilation)

---

## Integration with Flight Search App

Once voice-to-text is working, integrate with the flight search:

### Step 1: Run Voice-to-Text Server
```bash
cd voice-to-text-mcp
./target/release/voice-to-text-mcp --mcp-server models/ggml-base.en.bin
```

### Step 2: Connect Flight Search App
The original `flight_search_vtt.py` uses MCP to connect to voice-to-text:
```python
# The app connects via MCP protocol
# Voice input → Whisper transcription → Gemini parsing → Amadeus search
```

### Complete Voice-to-Flight Pipeline
```
User speaks → Whisper (voice-to-text) → Gemini AI (parse intent) → Amadeus API (search flights) → Results
```

---

## Recommended Testing Path

**For Quick Testing (5 minutes):**
1. Build on your Windows machine
2. Download `ggml-base.en.bin` model
3. Run: `./target/release/voice-to-text-mcp --timeout-ms 10000 models/ggml-base.en.bin`
4. Speak: "Find flights from LAX to JFK"
5. Verify transcription works

**For ARM Tablet Testing (30 minutes):**
1. Install Termux on Android tablet
2. Install Rust and dependencies in Termux
3. Build voice-to-text in Termux
4. Download Whisper model
5. Test voice recording on tablet
6. Integrate with flight search Python app

**For Full Integration (1 hour):**
1. Set up voice-to-text MCP server
2. Configure flight search app to use MCP
3. Get valid API keys (Gemini + Amadeus)
4. Test end-to-end: Voice → Transcription → Flight Search → Results

---

## Next Steps

1. **Choose your testing environment:**
   - Windows (easiest)
   - ARM64 Docker (build verification only)
   - Android Termux (most realistic for tablets)

2. **Build the voice-to-text server**
3. **Download a Whisper model**
4. **Test basic recording**
5. **Integrate with flight search app**

## Files You Need

- `voice-to-text-mcp/`: Rust source code
- `models/ggml-base.en.bin`: Whisper model (download separately)
- Microphone/audio input device

---

**Status:** Voice-to-text agent is ready for testing on x86_64 and ARM64
**Recommended Model:** `ggml-base.en.bin` (142MB)
**Build Time:** 2-6 minutes (first build), <1 min (subsequent)
**Hardware Requirements:** Microphone, 500MB disk space for model
