@echo off
setlocal enabledelayedexpansion

title Innovexa — Localhost Application Runner

cd /d "%~dp0"

echo ====================================================================
echo        INNOVEXA — LAUNCH APPLICATION ON LOCALHOST
echo ====================================================================
echo.

:: 1. Check for Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python was not found in your system PATH!
        echo Please install Python 3.10+ from https://www.python.org/downloads/
        echo (Make sure to check "Add python.exe to PATH" during installation)
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

:: 2. Check if core dependencies are installed
!PYTHON_CMD! -c "import fastapi, uvicorn, sklearn, joblib" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [!] Missing dependencies detected.
    echo [*] Running install_requirements.bat to set up environment first...
    echo.
    call "%~dp0install_requirements.bat"
    if !ERRORLEVEL! neq 0 (
        echo [ERROR] Automatic dependency installation failed.
        pause
        exit /b 1
    )
)

:: 3. Launch application via orchestrator
!PYTHON_CMD! "%~dp0launch_app.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo Application stopped.
)
pause
