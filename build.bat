@echo off
REM ============================================================================
REM MARVEL TRADING DASHBOARD - BUILD EXECUTABLE
REM ============================================================================
REM 
REM This script builds the Marvel trading dashboard into a Windows executable.
REM Requirements:
REM   - Python 3.12+
REM   - All dependencies installed (run: pip install -r requirements.txt)
REM
REM Run this from the project root directory:
REM   C:\path\to\marvel> build.bat

echo.
echo ============================================================================
echo MARVEL TRADING DASHBOARD - WINDOWS EXECUTABLE BUILD
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.12+ and add to PATH.
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version

echo.
echo [2/5] Checking PyInstaller installation...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo WARNING: PyInstaller not found. Installing...
    python -m pip install pyinstaller
)

echo.
echo [3/5] Installing/updating dependencies...
python -m pip install -r requirements.txt

echo.
echo [4/5] Building executable...
echo NOTE: This may take 2-5 minutes...
echo.

REM Ensure any running executable is stopped and the target file is removable.
set "TARGET_EXE=dist\MarvelTradingDashboard.exe"
set "MAX_RETRIES=10"
set "RETRY_DELAY=3"

echo Checking for running MarvelTradingDashboard process and attempting to stop it...
powershell -NoProfile -Command "Get-Process -Name 'MarvelTradingDashboard' -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }" >NUL 2>&1

echo Waiting a moment for OS to release handles...
timeout /t 2 /nobreak >NUL

if exist "%TARGET_EXE%" (
    echo Found existing %TARGET_EXE%. Attempting to delete before build...
    setlocal enabledelayedexpansion
    set /a i=0
    :del_loop
    del /f /q "%TARGET_EXE%" >NUL 2>&1
    if not exist "%TARGET_EXE%" (
        endlocal
        echo Successfully removed existing executable.
        goto BUILD_START
    )
    set /a i+=1
    if !i! GEQ %MAX_RETRIES% (
        endlocal
        echo WARNING: Could not delete %TARGET_EXE% after %MAX_RETRIES% attempts.
        echo Will build to temporary output folder `dist_temp` instead.
        goto BUILD_TEMP
    )
    echo Retry !i!/%MAX_RETRIES%: waiting %RETRY_DELAY% seconds before next delete attempt...
    timeout /t %RETRY_DELAY% /nobreak >NUL
    goto del_loop
) else (
    goto BUILD_START
)

:BUILD_START
echo Preparing build environment...
echo Building executable into final `dist` folder...
python -m PyInstaller marvel.spec --distpath=dist --workpath=build --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Check error messages above.
    pause
    exit /b 1
)
goto BUILD_DONE

:BUILD_TEMP
echo Building executable into temporary folder `dist_temp`...
python -m PyInstaller marvel.spec --distpath=dist_temp --workpath=build --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Temporary build failed. Check error messages above.
    pause
    exit /b 1
)
echo Temporary build completed: dist_temp\MarvelTradingDashboard.exe
echo Attempting to move temporary build into `dist`...
powershell -NoProfile -Command "if (-not (Test-Path 'dist')) { New-Item -ItemType Directory -Path 'dist' | Out-Null }; Start-Sleep -Seconds 1"
set "TEMP_EXE=dist_temp\MarvelTradingDashboard.exe"
if exist "%TEMP_EXE%" (
    move /Y "%TEMP_EXE%" "%TARGET_EXE%" >NUL 2>&1
    if errorlevel 1 (
        echo WARNING: Could not move temporary exe into final location. The target may still be locked.
        echo The temporary build is available at: dist_temp\MarvelTradingDashboard.exe
        echo Please stop any running instances or run this script as Administrator, then move the file manually.
    ) else (
        echo Moved temporary build into dist\MarvelTradingDashboard.exe
    )
) else (
    echo ERROR: Temporary build output not found at %TEMP_EXE%
)

:BUILD_DONE

if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Check error messages above.
    pause
    exit /b 1
)

REM Cleanup build cache only
if exist build (
    rmdir /s /q build 2>NUL
)

echo.
echo ============================================================================
echo [5/5] Build Complete!
echo ============================================================================
echo.
echo SUCCESS! Your executable has been created:
echo   Location: dist\MarvelTradingDashboard.exe
echo.
echo To run the dashboard:
echo   1. Navigate to: dist\
echo   2. Double-click: MarvelTradingDashboard.exe
echo.
echo Or run from command line:
echo   dist\MarvelTradingDashboard.exe
echo.
echo ============================================================================
echo.

REM Give user option to open dist folder
echo Do you want to open the dist folder now? (Y/N)
set /p choice="Choice: "
if /i "%choice%"=="Y" (
    start explorer dist
)

pause
