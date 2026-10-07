@echo off
setlocal enabledelayedexpansion

title Innovexa — Setup & Requirements Installer

echo ====================================================================
echo        INNOVEXA — INSTALL PYTHON DEPENDENCIES
echo ====================================================================
echo.

:: 1. Check if Python is installed and available in PATH
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    where py >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Python is not detected in your system PATH!
        echo.
        echo Please follow these quick steps:
        echo   1. Download Python 3.10 or newer from: https://www.python.org/downloads/
        echo   2. Run the installer and check the box: "Add python.exe to PATH"
        echo   3. Restart this batch file after installation.
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

echo [*] Python detected:
!PYTHON_CMD! --version
echo.

:: 2. Upgrade pip to ensure smooth wheel builds
echo [*] Upgrading pip...
!PYTHON_CMD! -m pip install --upgrade pip --quiet
echo.

:: 3. Install requirements
echo [*] Installing required packages from requirements.txt...
echo     (FastAPI, Uvicorn, scikit-learn, joblib, pandas, numpy, networkx, python-louvain, pydantic)
echo.
!PYTHON_CMD! -m pip install -r "%~dp0requirements.txt"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Package installation encountered an error!
    echo Please review the output above or check your internet connection.
    pause
    exit /b 1
)

echo.
echo [*] Verifying installation of core machine learning and API libraries...
!PYTHON_CMD! -c "import fastapi, uvicorn, sklearn, joblib, pandas, numpy, networkx, community, pydantic; print('[+] All core dependencies imported successfully!')"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [WARNING] Some dependencies could not be imported cleanly.
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo   SETUP COMPLETE! ALL REQUIREMENTS ARE INSTALLED.
echo ====================================================================
echo.
echo   You can now launch the application at any time by double-clicking:
echo   run_application.bat
echo.
echo ====================================================================
echo.
pause
