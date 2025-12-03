# PowerShell script to set up Android ARM Tablet Emulator for Flight Agent
# Run as Administrator or with appropriate permissions

param(
    [string]$AndroidHome = "$env:LOCALAPPDATA\Android\Sdk",
    [string]$JavaHome = "$env:LOCALAPPDATA\Java\jdk-17"
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Green
Write-Host "Flight Agent - ARM Tablet Simulator Setup" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Create directories
$DownloadDir = "$env:TEMP\android_setup"
New-Item -ItemType Directory -Force -Path $DownloadDir | Out-Null
New-Item -ItemType Directory -Force -Path $AndroidHome | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $JavaHome -Parent) | Out-Null

# Step 1: Download and install OpenJDK 17
Write-Host "[1/7] Installing Java JDK 17..." -ForegroundColor Cyan
if (-not (Test-Path $JavaHome)) {
    $JdkUrl = "https://download.java.net/java/GA/jdk17.0.2/dfd4a8d0985749f896bed50d7138ee7f/8/GPL/openjdk-17.0.2_windows-x64_bin.zip"
    $JdkZip = "$DownloadDir\openjdk-17.zip"

    Write-Host "  Downloading OpenJDK 17..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $JdkUrl -OutFile $JdkZip -UseBasicParsing

    Write-Host "  Extracting JDK..." -ForegroundColor Yellow
    Expand-Archive -Path $JdkZip -DestinationPath (Split-Path $JavaHome -Parent) -Force

    # Rename to expected path
    $ExtractedPath = Get-ChildItem -Path (Split-Path $JavaHome -Parent) -Filter "jdk-*" | Select-Object -First 1
    if ($ExtractedPath.FullName -ne $JavaHome) {
        Move-Item -Path $ExtractedPath.FullName -Destination $JavaHome -Force
    }

    Write-Host "  Java installed to: $JavaHome" -ForegroundColor Green
} else {
    Write-Host "  Java already installed" -ForegroundColor Green
}

# Set JAVA_HOME environment variable
$env:JAVA_HOME = $JavaHome
$env:PATH = "$JavaHome\bin;$env:PATH"
[Environment]::SetEnvironmentVariable("JAVA_HOME", $JavaHome, "User")

Write-Host "  Java version: $((& "$JavaHome\bin\java.exe" -version 2>&1)[0])" -ForegroundColor Green

# Step 2: Download Android Command Line Tools
Write-Host ""
Write-Host "[2/7] Installing Android SDK..." -ForegroundColor Cyan
$CmdlineToolsPath = "$AndroidHome\cmdline-tools\latest"
if (-not (Test-Path "$CmdlineToolsPath\bin\sdkmanager.bat")) {
    $AndroidToolsUrl = "https://dl.google.com/android/repository/commandlinetools-win-9477386_latest.zip"
    $AndroidToolsZip = "$DownloadDir\commandlinetools.zip"

    Write-Host "  Downloading Android command-line tools..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $AndroidToolsUrl -OutFile $AndroidToolsZip -UseBasicParsing

    Write-Host "  Extracting..." -ForegroundColor Yellow
    Expand-Archive -Path $AndroidToolsZip -DestinationPath "$AndroidHome\cmdline-tools-temp" -Force

    # Move to correct location
    New-Item -ItemType Directory -Force -Path "$AndroidHome\cmdline-tools" | Out-Null
    Move-Item -Path "$AndroidHome\cmdline-tools-temp\cmdline-tools" -Destination $CmdlineToolsPath -Force
    Remove-Item -Path "$AndroidHome\cmdline-tools-temp" -Recurse -Force

    Write-Host "  Android SDK tools installed" -ForegroundColor Green
} else {
    Write-Host "  Android SDK tools already installed" -ForegroundColor Green
}

# Set ANDROID_HOME environment variable
$env:ANDROID_HOME = $AndroidHome
$env:PATH = "$CmdlineToolsPath\bin;$AndroidHome\platform-tools;$AndroidHome\emulator;$env:PATH"
[Environment]::SetEnvironmentVariable("ANDROID_HOME", $AndroidHome, "User")

# Step 3: Accept licenses
Write-Host ""
Write-Host "[3/7] Accepting Android SDK licenses..." -ForegroundColor Cyan
$yes | & "$CmdlineToolsPath\bin\sdkmanager.bat" --licenses 2>&1 | Out-Null

# Step 4: Install required SDK components
Write-Host ""
Write-Host "[4/7] Installing Android SDK components..." -ForegroundColor Cyan
Write-Host "  This may take 10-15 minutes..." -ForegroundColor Yellow

$SdkComponents = @(
    "platform-tools",
    "platforms;android-33",
    "build-tools;33.0.2",
    "emulator",
    "system-images;android-33;google_apis;arm64-v8a"
)

foreach ($component in $SdkComponents) {
    Write-Host "  Installing $component..." -ForegroundColor Yellow
    & "$CmdlineToolsPath\bin\sdkmanager.bat" $component 2>&1 | Out-Null
}

Write-Host "  SDK components installed" -ForegroundColor Green

# Step 5: Create ARM64 Tablet AVD
Write-Host ""
Write-Host "[5/7] Creating ARM64 tablet emulator..." -ForegroundColor Cyan

$AvdName = "FlightAgent_ARM_Tablet"
$AvdPath = "$env:USERPROFILE\.android\avd\$AvdName.avd"

# Check if AVD already exists
$ExistingAvds = & "$CmdlineToolsPath\bin\avdmanager.bat" list avd 2>&1 | Select-String $AvdName
if ($ExistingAvds) {
    Write-Host "  Deleting existing AVD..." -ForegroundColor Yellow
    & "$CmdlineToolsPath\bin\avdmanager.bat" delete avd -n $AvdName 2>&1 | Out-Null
}

Write-Host "  Creating new ARM64 tablet AVD..." -ForegroundColor Yellow
$CreateAvdCommand = @"
echo no | "$CmdlineToolsPath\bin\avdmanager.bat" create avd -n $AvdName -k "system-images;android-33;google_apis;arm64-v8a" -d "pixel_tablet" --force
"@

Invoke-Expression $CreateAvdCommand 2>&1 | Out-Null

# Configure AVD settings
$ConfigIni = @"
hw.cpu.arch=arm64
hw.cpu.ncore=4
hw.ramSize=4096
hw.lcd.density=320
hw.lcd.width=1600
hw.lcd.height=2560
disk.dataPartition.size=4G
hw.keyboard=yes
hw.audioInput=yes
"@

if (Test-Path $AvdPath) {
    Add-Content -Path "$AvdPath\config.ini" -Value $ConfigIni
    Write-Host "  ARM64 tablet emulator created: $AvdName" -ForegroundColor Green
} else {
    Write-Host "  Warning: AVD may not have been created properly" -ForegroundColor Yellow
}

# Step 6: Create helper scripts
Write-Host ""
Write-Host "[6/7] Creating helper scripts..." -ForegroundColor Cyan

# Create launch emulator script
$LaunchScript = @"
@echo off
echo Starting ARM Tablet Emulator...
echo.
set ANDROID_HOME=$AndroidHome
set PATH=$AndroidHome\emulator;$AndroidHome\platform-tools;%PATH%
emulator -avd $AvdName -no-snapshot-load
"@
Set-Content -Path "launch_tablet_emulator.bat" -Value $LaunchScript
Write-Host "  Created: launch_tablet_emulator.bat" -ForegroundColor Green

# Create ADB install script
$AdbScript = @"
@echo off
echo Waiting for device...
adb wait-for-device
echo Device connected!
echo.
echo Installing Termux...
adb install -r termux_arm64.apk
echo.
echo Pushing flight_agent files...
adb push flight_agent_termux.tar.gz /sdcard/
echo.
echo Done! Now open Termux on the tablet and run:
echo   cd /sdcard
echo   tar -xzf flight_agent_termux.tar.gz
echo   cd flight_agent
echo   ./setup_termux.sh
"@
Set-Content -Path "deploy_to_tablet.bat" -Value $AdbScript
Write-Host "  Created: deploy_to_tablet.bat" -ForegroundColor Green

# Step 7: Create Termux deployment package
Write-Host ""
Write-Host "[7/7] Creating Termux deployment package..." -ForegroundColor Cyan

# Create Termux setup script
$TermuxSetup = @"
#!/data/data/com.termux/files/usr/bin/bash
# Termux setup script for Flight Agent on ARM tablet

echo "========================================="
echo "Flight Agent - Termux Setup"
echo "========================================="
echo ""

# Update packages
echo "[1/5] Updating Termux packages..."
pkg update -y
pkg upgrade -y

# Install dependencies
echo "[2/5] Installing dependencies..."
pkg install -y \
    python \
    rust \
    binutils \
    clang \
    openssl \
    libffi \
    portaudio \
    git \
    wget

# Create Python virtual environment
echo "[3/5] Setting up Python environment..."
python -m venv .venv
source .venv/bin/activate

# Install Python packages
echo "[4/5] Installing Python packages..."
pip install --upgrade pip
pip install -r requirements_termux.txt

# Build Rust components
echo "[5/5] Building voice-to-text MCP server..."
cd voice-to-text-mcp
cargo build --release --target aarch64-linux-android
cd ..

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To use:"
echo "1. Edit .env with your API keys"
echo "2. source .venv/bin/activate"
echo "3. python flight_search_vtt.py --voice"
"@
Set-Content -Path "$env:TEMP\setup_termux.sh" -Value $TermuxSetup

Write-Host "  Created Termux setup script" -ForegroundColor Green

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Environment variables set:" -ForegroundColor Cyan
Write-Host "  JAVA_HOME: $env:JAVA_HOME" -ForegroundColor White
Write-Host "  ANDROID_HOME: $env:ANDROID_HOME" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Download Termux ARM64 APK from: https://f-droid.org/en/packages/com.termux/" -ForegroundColor White
Write-Host "  2. Run: .\launch_tablet_emulator.bat" -ForegroundColor White
Write-Host "  3. Wait for emulator to fully boot (2-3 minutes)" -ForegroundColor White
Write-Host "  4. Install Termux on the emulator" -ForegroundColor White
Write-Host "  5. Deploy flight_agent using deploy_to_tablet.bat" -ForegroundColor White
Write-Host ""
Write-Host "To start emulator now, run: .\launch_tablet_emulator.bat" -ForegroundColor Yellow
Write-Host ""

# Cleanup
Remove-Item -Path $DownloadDir -Recurse -Force -ErrorAction SilentlyContinue
