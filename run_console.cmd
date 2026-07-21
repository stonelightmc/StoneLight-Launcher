@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found.
    echo Run setup.cmd first.
    echo.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" launcher_console.py
echo.
pause
