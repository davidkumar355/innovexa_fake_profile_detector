@echo off
cd /d "%~dp0"
if exist "%~dp0Project Work\install_requirements.bat" (
    call "%~dp0Project Work\install_requirements.bat"
) else (
    echo [ERROR] Could not find Project Work\install_requirements.bat!
    pause
)
