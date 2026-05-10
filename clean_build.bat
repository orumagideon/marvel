@echo off
REM ============================================================================
REM MARVEL TRADING DASHBOARD - CLEAN BUILD SCRIPT
REM ============================================================================
REM
REM This script completely cleans all build artifacts and starts fresh.
REM Use this if the normal build fails due to file locks.
REM
REM Run from the project root:
REM   C:\path\to\marvel> clean_build.bat

echo.
echo ============================================================================
echo MARVEL TRADING DASHBOARD - COMPLETE CLEAN BUILD
echo ============================================================================
echo.

REM Terminate running instances
echo [1/4] Stopping running instances...
taskkill /F /IM MarvelTradingDashboard.exe /T >NUL 2>&1
taskkill /F /FI "MODULES eq *marvel*" /T >NUL 2>&1
ping -n 3 127.0.0.1 >NUL 2>&1

REM Remove all build artifacts
echo [2/4] Removing all build directories...
if exist dist (
    echo Removing dist directory...
    rmdir /s /q dist 2>NUL
)
if exist build (
    echo Removing build directory...
    rmdir /s /q build 2>NUL
)
if exist dist_staging (
    echo Removing dist_staging directory...
    rmdir /s /q dist_staging 2>NUL
)
if exist build_staging (
    echo Removing build_staging directory...
    rmdir /s /q build_staging 2>NUL
)

REM Wait for cleanup
ping -n 2 127.0.0.1 >NUL 2>&1

REM Verify cleanup
echo [3/4] Verifying cleanup...
if exist dist (
    echo WARNING: dist directory still exists
) else (
    echo ✓ dist directory removed
)
if exist build (
    echo WARNING: build directory still exists
) else (
    echo ✓ build directory removed
)

REM Start fresh build
echo [4/4] Starting fresh build...
call build.bat

pause
