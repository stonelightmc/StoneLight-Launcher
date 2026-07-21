@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    call setup.cmd
    if errorlevel 1 pause & exit /b 1
)

".venv\Scripts\python.exe" bootstrap.py
if errorlevel 1 pause
