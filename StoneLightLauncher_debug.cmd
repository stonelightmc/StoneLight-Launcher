@echo off
setlocal
cd /d "%~dp0"

echo === StoneLight Launcher v0.5.35 debug run ===
echo Project dir: %CD%
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Running setup...
    call setup.cmd
    if errorlevel 1 (
        echo.
        echo ERROR: setup failed.
        pause
        exit /b 1
    )
)

echo Python:
".venv\Scripts\python.exe" --version
echo.

echo Pip:
".venv\Scripts\python.exe" -m pip --version
echo.

echo Checking imports:
".venv\Scripts\python.exe" -c "import requests, minecraft_launcher_lib, customtkinter; print('All imports OK')"
echo Import check exit code: %ERRORLEVEL%
echo.

echo Installed packages:
".venv\Scripts\python.exe" -m pip freeze
echo.

echo Starting bootstrap...
".venv\Scripts\python.exe" bootstrap.py

echo.
echo Process finished with code %ERRORLEVEL%
pause
