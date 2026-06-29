@echo off
setlocal
cd /d "%~dp0"

echo === StoneLight Launcher v0.5.24 setup ===
echo Project dir: %CD%
echo.

if exist ".venv\Scripts\python.exe" (
    echo Existing venv found.
    echo It will be reused and dependencies will be repaired.
    goto INSTALL_DEPS
)

echo Creating virtual environment...
py -3.13 -m venv .venv
if not errorlevel 1 goto INSTALL_DEPS

echo Python 3.13 failed or not found, trying Python 3.12...
py -3.12 -m venv .venv
if not errorlevel 1 goto INSTALL_DEPS

echo Python 3.12 failed or not found, trying default py...
py -m venv .venv
if not errorlevel 1 goto INSTALL_DEPS

echo Default py failed or not found, trying python...
python -m venv .venv
if not errorlevel 1 goto INSTALL_DEPS

echo.
echo ERROR: Could not create virtual environment.
echo Install Python 3.13 or 3.12 and enable "Add python.exe to PATH".
echo.
pause
exit /b 1

:INSTALL_DEPS
if not exist ".venv\Scripts\python.exe" (
    echo.
    echo ERROR: .venv\Scripts\python.exe not found.
    echo Delete the .venv folder and run this setup again.
    echo.
    pause
    exit /b 1
)

echo.
echo Installing or repairing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto PIP_ERROR

".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto PIP_ERROR

echo.
echo Verifying dependencies...
".venv\Scripts\python.exe" -c "import requests, minecraft_launcher_lib, customtkinter; print('Dependencies OK')"
if errorlevel 1 goto PIP_ERROR

echo.
echo Setup complete.
echo Run StoneLightLauncher.cmd
echo.
pause
exit /b 0

:PIP_ERROR
echo.
echo ERROR: dependency setup failed.
echo Copy the full console output and send it for debugging.
echo.
pause
exit /b 1
