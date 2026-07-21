@echo off
setlocal
cd /d "%~dp0"

if exist "StoneLightLauncher_silent.vbs" (
    wscript.exe //nologo "StoneLightLauncher_silent.vbs"
    exit /b %ERRORLEVEL%
)

if not exist ".venv\Scripts\pythonw.exe" (
    call setup.cmd
    if errorlevel 1 pause & exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" "bootstrap_web.py"
exit /b 0
