@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
    call setup.cmd
    if errorlevel 1 pause & exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" "StoneLightLauncherWeb.pyw" --browser
exit /b 0
