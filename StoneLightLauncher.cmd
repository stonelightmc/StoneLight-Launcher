@echo off
setlocal
cd /d "%~dp0"

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

".venv\Scripts\python.exe" bootstrap.py

if errorlevel 1 (
    echo.
    echo ERROR: Launcher crashed or dependencies could not be installed.
    echo Run StoneLightLauncher_debug.cmd for more details.
    echo.
    pause
    exit /b 1
)
