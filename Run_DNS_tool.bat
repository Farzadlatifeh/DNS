@echo off
setlocal EnableDelayedExpansion

:: ==============================================================================
:: 1. AUTOMATIC ADMINISTRATOR ELEVATION
:: ==============================================================================
net session >nul 2>&1
if !errorLevel! neq 0 (
    echo Requesting Administrator privileges...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd.exe -ArgumentList '/c \"%~f0\"' -Verb RunAs"
    exit /b
)

:: ==============================================================================
:: 2. ENVIRONMENT SETUP
:: ==============================================================================
cd /d "%~dp0"
set "SCRIPT_NAME=dns_manager_gui.py"

if not exist "%SCRIPT_NAME%" (
    echo [ERROR] Python script '%SCRIPT_NAME%' not found in this directory.
    echo Please ensure the .bat file and the .py file are in the same folder.
    pause
    exit /b 1
)

:: ==============================================================================
:: 3. PYTHON DETECTION
:: ==============================================================================
where py >nul 2>&1
if !errorLevel! equ 0 (
    set "PYTHON_CMD=py"
) else (
    set "PYTHON_CMD=python"
)

:: ==============================================================================
:: 4. EXECUTION
:: ==============================================================================
echo ============================================================
echo  Applying DNS Configuration...
echo ============================================================
echo(

%PYTHON_CMD% "%SCRIPT_NAME%"
set "PY_EXIT_CODE=!errorLevel!"

:: ==============================================================================
:: 5. COMPLETION HANDLING (Bulletproof blank lines and error checking)
:: ==============================================================================
echo(
if !PY_EXIT_CODE! neq 0 (
    echo [ERROR] Script finished with errors ^(Code: !PY_EXIT_CODE!^).
) else (
    echo [SUCCESS] Script completed successfully.
)
echo(
echo Press any key to close this window...
pause >nul