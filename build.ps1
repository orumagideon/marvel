# ============================================================================
# MARVEL TRADING DASHBOARD - BUILD EXECUTABLE (PowerShell)
# ============================================================================
#
# Run this PowerShell script to build the Windows executable.
# From PowerShell:
#   .\build.ps1
#
# If you get execution policy error, run first:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#
# ============================================================================

Write-Host ""
Write-Host "============================================================================"
Write-Host "MARVEL TRADING DASHBOARD - WINDOWS EXECUTABLE BUILD"
Write-Host "============================================================================"
Write-Host ""

# Check Python
Write-Host "[1/5] Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion"
}
catch {
    Write-Host "ERROR: Python not found. Please install Python 3.12+ and add to PATH." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check PyInstaller
Write-Host ""
Write-Host "[2/5] Checking PyInstaller..."
$pyInstallerCheck = python -m pip show pyinstaller 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    python -m pip install pyinstaller
}
else {
    Write-Host "PyInstaller found" -ForegroundColor Green
}

# Install dependencies
Write-Host ""
Write-Host "[3/5] Installing/updating dependencies..."
pip install -r requirements.txt

# Clean old builds
Write-Host ""
Write-Host "[4/5] Cleaning old builds..."
if (Test-Path "dist\Marvel") {
    Remove-Item -Path "dist\Marvel" -Recurse -Force
    Write-Host "  Removed old dist\Marvel"
}
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
    Write-Host "  Removed old build"
}

# Build
Write-Host ""
Write-Host "[5/5] Building executable..."
Write-Host "This may take 2-5 minutes..."
Write-Host ""

pyinstaller marvel.spec --distpath=dist --buildpath=build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Build failed. Check error messages above." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "============================================================================"
Write-Host "BUILD COMPLETE!" -ForegroundColor Green
Write-Host "============================================================================"
Write-Host ""
Write-Host "SUCCESS! Your executable has been created:" -ForegroundColor Green
Write-Host ""
Write-Host "  Location: dist\Marvel\Marvel.exe"
Write-Host ""
Write-Host "To run the dashboard:"
Write-Host "  1. Navigate to: dist\Marvel\"
Write-Host "  2. Double-click: Marvel.exe"
Write-Host ""
Write-Host "Or run from PowerShell:"
Write-Host "  .\dist\Marvel\Marvel.exe"
Write-Host ""
Write-Host "============================================================================"
Write-Host ""

$openFolder = Read-Host "Do you want to open the dist folder? (Y/N)"
if ($openFolder -eq "Y" -or $openFolder -eq "y") {
    explorer dist
}

Write-Host "Build complete!"
Read-Host "Press Enter to exit"
