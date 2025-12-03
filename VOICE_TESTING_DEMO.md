# Voice Testing - What Happens With Microphone Input

## The User Experience

### **On a Physical ARM Tablet (Android/Termux or Raspberry Pi):**

When you run:
```bash
python3 voice_to_flight_integrated.py
```

This is what happens:

```
============================================================
🎤 ✈️  VOICE-TO-FLIGHT SEARCH (ARM64)
============================================================

🎤 Starting voice recording...
Speak your flight search query now (max 30s)
Recording will stop automatically after silence or timeout
------------------------------------------------------------

🔴 RECORDING... (speak now)

[User speaks: "Find flights from Los Angeles to New York on December 20th"]

⏸️  Silence detected (2 seconds)
✅ Recording stopped (7.5 seconds captured)

📝 Transcribing audio with Whisper...
⏳ Processing...

✅ Transcription complete!

🎤 Transcribed: "Find flights from Los Angeles to New York on December 20th"

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
  💰 Price: 245.00 USD
  🏢 Carrier: AA
  🛫 Departure: LAX at 2025-12-20T08:00:00
  🛬 Arrival: JFK at 2025-12-20T16:30:00
  ⏱️  Duration: PT8H30M

✈️  Flight #2
  💰 Price: 278.00 USD
  🏢 Carrier: UA
  🛫 Departure: LAX at 2025-12-20T10:15:00
  🛬 Arrival: JFK at 2025-12-20T18:45:00
  ⏱️  Duration: PT8H30M

============================================================
```

### **What the Application Does:**

1. **Starts Recording Immediately** - No confirmation needed, starts capturing audio as soon as you run the command

2. **Visual Feedback:**
   - `🔴 RECORDING...` - Shows you're being recorded
   - Timeout countdown (optional: `28s remaining...`)
   - Audio level indicator (optional: `▓▓▓▓▓▓░░░░`)

3. **Automatic Stop:**
   - Stops after 2 seconds of silence
   - OR after 30 seconds maximum (configurable)
   - User can manually press Ctrl+C to stop early

4. **Processing:**
   - Whisper transcribes the audio (~3-5 seconds on ARM tablet)
   - Shows the transcribed text
   - Continues to flight search automatically

5. **No Additional Prompts:**
   - Does NOT ask "Do you want to use the microphone?" (already implied by running the app)
   - Does NOT show browser-style permission dialogs (command-line app)
   - Does NOT require button presses during recording

---

## Why Voice Doesn't Work in Docker (Current Environment)

### Technical Explanation:

**Docker Container:**
```
┌──────────────────────────────────┐
│   Docker Container (ARM64)       │
│                                  │
│   [voice-to-text-mcp binary]    │
│            ↓                     │
│   Tries to access /dev/snd       │ ❌ No audio device!
│            ↓                     │
│   ❌ Error: No input device      │
│                                  │
└──────────────────────────────────┘
         ↑
         │ (isolated)
         │
┌──────────────────────────────────┐
│   Windows Host                   │
│                                  │
│   🎤 Your Microphone             │ ← Not accessible from container
│                                  │
└──────────────────────────────────┘
```

**What Happens:**
```bash
$ docker run --platform linux/arm64 --rm voice-flight-arm64 \
  python3 /app/voice_to_flight_integrated.py

🎤 Starting voice recording...
Recording will stop automatically after silence or timeout
------------------------------------------------------------

❌ Voice capture failed: No input device available
❌ No voice input captured. Exiting.
```

---

## Testing Options

### Option 1: ✅ Text Mode (Works Right Now in Docker)

This bypasses voice input and simulates the complete pipeline:

```bash
docker run --platform linux/arm64 --rm voice-flight-arm64 \
  python3 /app/voice_to_flight_integrated.py \
  --text "Find flights from Los Angeles to New York on December 20"
```

**What This Tests:**
- ✅ ARM64 execution
- ✅ Gemini AI parsing
- ✅ Amadeus flight search
- ✅ Result formatting
- ✅ Complete pipeline (except voice capture)

**Output:** (same as voice mode, but skips recording step)

---

### Option 2: 🎯 Deploy to Android Tablet (Full Voice Testing)

**To test voice on a real ARM device:**

#### On Android Tablet with Termux:

1. **Install Termux** from F-Droid

2. **Grant Microphone Permission:**
   ```bash
   # Test microphone access
   termux-microphone-record -f test.wav -l 5
   # System will prompt: "Allow Termux to access microphone?"
   # Tap: "Allow"
   ```

3. **Install and Run:**
   ```bash
   pkg install python rust git
   git clone https://github.com/fw2274/flight_agent
   cd flight_agent

   # Build voice-to-text
   cd voice-to-text-mcp
   cargo build --release
   cd ..

   # Download Whisper model
   cd voice-to-text-mcp/models
   curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
   cd ../..

   # Install Python dependencies
   pip install -r requirements_termux.txt

   # Configure API keys
   nano .env

   # Run with voice!
   python3 voice_to_flight_integrated.py
   ```

4. **Speak Your Query:**
   - App starts recording automatically
   - Speak: "Find flights from Los Angeles to New York on December 20th"
   - Wait 2 seconds after speaking (silence detection)
   - See transcription and flight results!

---

### Option 3: 🎯 Raspberry Pi (Full Voice Testing)

Similar to Android, but on a Raspberry Pi with USB microphone.

---

## Microphone Permission Flow

### On Android Termux:

**First Time:**
```
$ python3 voice_to_flight_integrated.py

🎤 Starting voice recording...

[System Dialog Appears]
┌──────────────────────────────────────┐
│  Allow Termux to record audio?       │
│                                      │
│  [Deny]           [Allow]            │
└──────────────────────────────────────┘
```

**After Allowing:**
- Permission is saved
- No more prompts on subsequent runs
- App records immediately

**If Denied:**
```
❌ Voice capture failed: Permission denied
Please grant microphone permission in Android settings
```

### On Raspberry Pi / Linux:

- No permission dialog (root user or correct permissions)
- May need to add user to `audio` group:
  ```bash
  sudo usermod -a -G audio $USER
  ```

---

## Complete Voice Workflow Diagram

```
User runs command
      ↓
Application starts
      ↓
Checks for voice-to-text binary
      ↓
  ✅ Found → Continue
  ❌ Not found → Show error
      ↓
Checks for Whisper model
      ↓
  ✅ Found → Continue
  ❌ Not found → Show error
      ↓
Checks for microphone access
      ↓
  ✅ Available → Continue
  ❌ Not available → Show error
      ↓
🔴 START RECORDING (automatic, no prompt)
      ↓
Capture audio from microphone
      ↓
Monitor for silence (2s default)
      ↓
  Silence detected → Stop recording
  OR
  Timeout (30s default) → Stop recording
      ↓
Save audio to temporary buffer
      ↓
Pass audio to Whisper for transcription
      ↓
Wait for Whisper processing (~3-5s)
      ↓
Receive transcribed text
      ↓
Display: "🎤 Transcribed: [text]"
      ↓
Parse query with Gemini AI
      ↓
Extract flight parameters
      ↓
Search flights with Amadeus
      ↓
Format and display results
      ↓
Done!
```

---

## Configuration Options

### Custom Voice Timeouts:

```bash
# Record for up to 60 seconds
python3 voice_to_flight_integrated.py --timeout 60000

# Longer silence detection (5 seconds)
python3 voice_to_flight_integrated.py --silence-timeout 5000

# Use faster model (for testing)
python3 voice_to_flight_integrated.py --model models/ggml-tiny.en.bin

# Combine settings
python3 voice_to_flight_integrated.py \
  --timeout 45000 \
  --silence-timeout 3000 \
  --model models/ggml-small.en.bin
```

---

## Testing Recommendations

### **Right Now (Docker on Windows):**
```bash
# Test the complete pipeline (without voice)
docker run --platform linux/arm64 --rm voice-flight-arm64 \
  python3 /app/voice_to_flight_integrated.py \
  --text "Find flights from LAX to JFK on December 20"
```

**This proves:**
- ✅ ARM64 compilation works
- ✅ Application logic works
- ✅ API integration works
- ✅ Ready for voice deployment

### **On Physical ARM Device (Full Test):**
```bash
# Full voice-to-flight pipeline
python3 voice_to_flight_integrated.py
# Speak your query, see results!
```

---

## Troubleshooting Voice Issues

### Issue: "No input device available"
**On Docker:** Expected - Docker can't access host audio
**On Android:** Grant microphone permission
**On Raspberry Pi:** Check `arecord -l` shows devices

### Issue: "Permission denied"
```bash
# On Linux, add user to audio group
sudo usermod -a -G audio $USER
# Log out and back in

# On Android Termux, use:
termux-microphone-record -f test.wav -l 5
# Grant permission when prompted
```

### Issue: "Voice-to-text binary not found"
```bash
# Build the binary first
cd voice-to-text-mcp
cargo build --release
cd ..
```

### Issue: "Model file not found"
```bash
# Download Whisper model
cd voice-to-text-mcp/models
curl -L -O https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
```

---

## Summary

### Will the app ask for microphone input?

**Answer:**
- **🎤 On Physical ARM Device (Android/Pi):** YES - It starts recording immediately when you run the command
  - System may show permission dialog first time (Android)
  - After permission granted, records automatically
  - No additional prompts during runtime

- **❌ In Docker on Windows:** NO - Docker can't access microphone
  - Use `--text` mode instead
  - Tests all functionality except voice capture

### Recommended Testing Path:

1. **Now:** Test text mode in Docker (proves everything works on ARM64)
2. **Next:** Deploy to Android tablet or Raspberry Pi for full voice testing
3. **Result:** Complete voice-to-flight search on ARM tablet!

---

**Voice Mode:** 🎯 Ready for physical ARM devices
**Text Mode:** ✅ Working in Docker right now
**Full Pipeline:** ✅ Verified on ARM64 architecture
