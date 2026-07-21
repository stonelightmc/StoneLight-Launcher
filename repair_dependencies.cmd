@echo off
setlocal
cd /d "%~dp0"

echo === StoneLight Launcher dependency repair ===
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Running setup...
    call setup.cmd
    exit /b %ERRORLEVEL%
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" -c "import requests, minecraft_launcher_lib, customtkinter; print('Dependencies OK')"

echo.
pause
