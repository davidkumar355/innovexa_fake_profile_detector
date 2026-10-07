@echo off
cd /d "%~dp0"
if exist "%~dp0Project Work\run_application.bat" (
    call "%~dp0Project Work\run_application.bat"
) else (
    echo [ERROR] Could not find Project Work\run_application.bat!
    pause
)
