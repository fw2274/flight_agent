# Testing Voice-to-Text on Windows (Outside Docker)

This guide shows how to test the voice-to-text MCP server on your Windows machine with your actual microphone.

## Prerequisites

### Step 1: Install Rust

1. **Download Rust installer:**
   - Visit: https://rustup.rs/
   - Or direct download: https://static.rust-lang.org/rustup/dist/x86_64-pc-windows-msvc/rustup-init.exe

2. **Run the installer:**
   ```cmd
   # Download and run rustup-init.exe
   # Choose: "1) Proceed with installation (default)"
   ```

3. **Verify installation:**
   ```cmd
   rustc --version
   # Should show: rustc 1.x.x

   cargo --version
   # Should show: cargo 1.x.x
   ```

4. **Restart your terminal** (to refresh PATH)

---

## Build Voice-to-Text Binary

### Step 2: Build the Application

```cmd
cd C:\Users\ranan\flight_agent\voice-to-text-mcp

# Build for Windows (will take 2-6 minutes on first build)
cargo build --release
```

**What Happens:**
- Downloads Rust dependencies
- Compiles whisper-rs with Windows CUDA support (if NVIDIA GPU available)
- Creates binary: `target\release\voice-to-text-mcp.exe`

**Expected Output:**
```
   Compiling whisper-rs v0.14.3
   Compiling voice-to-text-mcp v0.1.0
    Finished release [optimized] target(s) in 3m 45s
```

---

## Download Whisper Model

### Step 3: Get a Whisper Model

```cmd
cd C:\Users\ranan\flight_agent\voice-to-text-mcp\models

# Download base model (recommended - 142MB)
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin

# Or download tiny model (faster, 75MB)
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin

cd ..
```

**Models Available:**
| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| ggml-tiny.en | 75MB | Fastest | Good | Quick testing |
| ggml-base.en | 142MB | Fast | Better | ⭐ Recommended |
| ggml-small.en | 466MB | Slower | Best | High accuracy |

---

## Test Voice-to-Text

### Step 4: Test with Your Microphone

#### Test 1: Simple 10-Second Recording
```cmd
cd C:\Users\ranan\flight_agent\voice-to-text-mcp

# Record for 10 seconds
.\target\release\voice-to-text-mcp.exe --timeout-ms 10000 models\ggml-base.en.bin
```

**What Happens:**
1. App starts and immediately begins recording from your default microphone
2. Speak something: "Testing voice to text functionality"
3. Recording stops after 2 seconds of silence OR 10 seconds timeout
4. Whisper transcribes the audio
5. Transcription is printed to console

**Expected Output:**
```
Recording started. Speak now...
[Speak your text]
Recording stopped after 5.2 seconds
Transcribing audio...
Transcription: "Testing voice to text functionality"
```

---

#### Test 2: Flight Search Query
```cmd
# 15-second recording
.\target\release\voice-to-text-mcp.exe --timeout-ms 15000 models\ggml-base.en.bin
```

**Speak:** "Find flights from Los Angeles to New York on December 20th"
**Expected:** "Find flights from Los Angeles to New York on December 20th"

---

#### Test 3: Debug Mode (Saves Audio File)
```cmd
# Record and save audio for inspection
.\target\release\voice-to-text-mcp.exe --debug --timeout-ms 10000 models\ggml-base.en.bin
```

**What This Does:**
- Records your voice
- Saves audio to `debug\audio_YYYYMMDD_HHMMSS_raw.wav`
- Saves processed audio to `debug\audio_YYYYMMDD_HHMMSS_processed.wav`
- You can play these files to verify recording quality

---

#### Test 4: Custom Settings
```cmd
# Longer recording with longer silence detection
.\target\release\voice-to-text-mcp.exe --timeout-ms 30000 --silence-timeout-ms 3000 models\ggml-base.en.bin

# No auto-stop (record for full duration)
.\target\release\voice-to-text-mcp.exe --no-auto-stop --timeout-ms 5000 models\ggml-base.en.bin

# Use faster model
.\target\release\voice-to-text-mcp.exe --timeout-ms 10000 models\ggml-tiny.en.bin
```

---

## Integrate with Flight Search

### Step 5: Test Complete Voice-to-Flight Pipeline (Windows)

Once voice-to-text is working, test the integrated application:

```cmd
cd C:\Users\ranan\flight_agent

# Install Python dependencies (if not already done)
pip install -r requirements_termux.txt

# Test voice-to-flight (will use voice-to-text binary)
python voice_to_flight_integrated.py --voice-binary .\voice-to-text-mcp\target\release\voice-to-text-mcp.exe --model voice-to-text-mcp\models\ggml-base.en.bin
```

**Full Pipeline:**
1. 🎤 Captures your voice from microphone
2. 📝 Whisper transcribes to text
3. 🧠 Gemini parses flight intent
4. ✈️ Amadeus searches flights
5. 📊 Displays results

---

## Troubleshooting

### Issue: "Rust not installed"
**Solution:**
```cmd
# Download and install from: https://rustup.rs/
# Or run:
winget install Rustlang.Rustup
```

### Issue: "cargo: command not found"
**Solution:**
- Restart your terminal after installing Rust
- Or manually add to PATH: `C:\Users\{YourUser}\.cargo\bin`

### Issue: "No input device available"
**Solution:**
- Check Windows Sound Settings → Input
- Ensure microphone is connected and not muted
- Set default recording device

**Test Microphone:**
```cmd
# Windows Voice Recorder app
soundrecorder
```

### Issue: "CUDA not found" warning
**Solution:**
- **If you have NVIDIA GPU:** Install CUDA Toolkit from https://developer.nvidia.com/cuda-downloads
- **If no NVIDIA GPU:** Ignore warning, will use CPU (slower but works)

### Issue: "Build failed" error
**Solution:**
```cmd
# Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/downloads/
# Select: "Desktop development with C++"

# Or install Windows SDK
```

### Issue: "Poor transcription quality"
**Solution:**
- Use better model: `ggml-small.en.bin`
- Reduce background noise
- Speak clearly and closer to microphone
- Check microphone quality in Windows settings

### Issue: "Transcription is slow"
**Solution:**
- Use faster model: `ggml-tiny.en.bin`
- Enable CUDA (if NVIDIA GPU): Install CUDA Toolkit
- First run is slower (model loading), subsequent runs faster

---

## Performance on Windows

### Expected Performance (on modern Windows PC):

| Operation | Time (CPU) | Time (NVIDIA GPU) |
|-----------|------------|-------------------|
| First Build | 3-6 minutes | 6-8 minutes (CUDA compile) |
| Subsequent Builds | <30 seconds | <30 seconds |
| Voice Capture (5s) | Real-time | Real-time |
| Whisper Transcription (5s audio) | 2-4 seconds | 1-2 seconds |
| **Total Pipeline** | **3-5 seconds** | **2-3 seconds** |

### Hardware Acceleration:

- **NVIDIA GPU (CUDA):** 2-3x faster transcription
- **Intel/AMD CPU:** Still fast enough for real-time use
- **Audio Capture:** Always real-time (no delay)

---

## Quick Testing Workflow

### Fastest Way to Test:

1. **Install Rust** (5 minutes):
   ```cmd
   # Download from: https://rustup.rs/
   # Run installer, choose default options
   ```

2. **Build Binary** (4 minutes):
   ```cmd
   cd C:\Users\ranan\flight_agent\voice-to-text-mcp
   cargo build --release
   ```

3. **Download Model** (2 minutes):
   ```cmd
   cd models
   curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
   cd ..
   ```

4. **Test Recording** (1 minute):
   ```cmd
   .\target\release\voice-to-text-mcp.exe --timeout-ms 10000 models\ggml-base.en.bin
   ```
   Speak: "Testing one two three"

**Total Time:** ~12 minutes from start to working voice-to-text!

---

## Example Test Session

```cmd
C:\Users\ranan\flight_agent\voice-to-text-mcp> .\target\release\voice-to-text-mcp.exe --timeout-ms 15000 models\ggml-base.en.bin

Recording started. Speak now...
[User speaks: "Find flights from Los Angeles to New York on December 20th"]
Recording stopped after 7.3 seconds

Transcribing audio...
Processing with Whisper base.en model...
Done!

Transcription: "Find flights from Los Angeles to New York on December 20th"

C:\Users\ranan\flight_agent\voice-to-text-mcp>
```

Perfect! The voice-to-text works outside Docker on Windows.

---

## Next: Test Complete Voice-to-Flight

Once voice-to-text is working, test the complete pipeline:

```cmd
cd C:\Users\ranan\flight_agent

# Make sure API keys are in .env
notepad .env

# Run integrated app
python voice_to_flight_integrated.py `
  --voice-binary .\voice-to-text-mcp\target\release\voice-to-text-mcp.exe `
  --model voice-to-text-mcp\models\ggml-base.en.bin `
  --timeout 15000
```

**Full Experience:**
- 🎤 App captures your voice
- 📝 Whisper transcribes
- 🧠 Gemini parses intent
- ✈️ Amadeus searches flights
- 📊 Results displayed

---

## Summary

**Advantages of Testing on Windows Host:**
- ✅ Access to real microphone
- ✅ Native x86_64 performance (faster than ARM64 Docker)
- ✅ CUDA acceleration (if NVIDIA GPU)
- ✅ See actual user experience
- ✅ Debug audio issues easily

**After Windows Testing:**
- Deploy to ARM tablet with confidence
- Know that voice capture works
- Understand user experience
- Have working baseline for comparison

---

**Status:** Ready to test voice-to-text on Windows
**Requirements:** Rust, Whisper model, Microphone
**Time to Setup:** ~12 minutes
**Performance:** 2-5 seconds per transcription
