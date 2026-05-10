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
REM Enable delayed expansion for safer variable handling in loops
setlocal ENABLEDELAYEDEXPANSION

REM Ensure no running instance is locking files. Attempt graceful then force kill.
echo Checking for running MarvelTradingDashboard.exe and attempting to stop it...
tasklist /FI "IMAGENAME eq MarvelTradingDashboard.exe" 2>NUL | find /I "MarvelTradingDashboard.exe" >NUL
if errorlevel 1 (
    echo No running MarvelTradingDashboard.exe found.
) else (
    echo Found running process. Attempting graceful termination...
    taskkill /IM MarvelTradingDashboard.exe /T >NUL 2>&1
    timeout /t 2 /nobreak >NUL
    tasklist /FI "IMAGENAME eq MarvelTradingDashboard.exe" 2>NUL | find /I "MarvelTradingDashboard.exe" >NUL
    if errorlevel 1 (
        echo Process terminated.
    ) else (
        echo Process still running. Forcing termination...
        taskkill /F /IM MarvelTradingDashboard.exe /T >NUL 2>&1
        timeout /t 1 /nobreak >NUL
    )
)

REM Remove old build directories (retry on failure)
set RETRIES=3
set COUNT=0
:CLEAN_LOOP
if exist dist\MarvelTradingDashboard (
    rmdir /s /q dist\MarvelTradingDashboard >NUL 2>&1
    if exist dist\MarvelTradingDashboard (
        set /A COUNT+=1
        if !COUNT! GEQ !RETRIES! (
            echo WARNING: Failed to remove dist\MarvelTradingDashboard after !RETRIES! attempts. You may need to close lingering processes or remove the folder manually.
        ) else (
            echo Retry removing dist\MarvelTradingDashboard (attempt !COUNT!/!RETRIES!)...
            timeout /t 1 /nobreak >NUL
            goto CLEAN_LOOP
        )
    ) else (
        echo Removed old dist\MarvelTradingDashboard folder.
    )
)
endlocal

if exist build rmdir /s /q build

REM Run PyInstaller using python -m
python -m PyInstaller marvel.spec --distpath=dist --workpath=build

if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Check error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo [5/5] Build Complete!
echo ============================================================================
echo.
echo SUCCESS! Your executable has been created:
echo   Location: dist\MarvelTradingDashboard\MarvelTradingDashboard.exe
echo.
echo To run the dashboard:
echo   1. Navigate to: dist\MarvelTradingDashboard\
echo   2. Double-click: MarvelTradingDashboard.exe
echo.
echo Or run from command line:
echo   dist\MarvelTradingDashboard\MarvelTradingDashboard.exe
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
