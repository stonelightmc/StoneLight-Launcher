@echo off
chcp 65001 >nul
title Build StoneLight Launcher EXE

echo.
echo ========================================
echo   StoneLight Launcher EXE Builder
echo ========================================
echo.
echo This script creates:
echo   dist\StoneLight Launcher\StoneLight Launcher.exe
echo.

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher "py" was not found.
  echo Install Python 3.11+ from python.org and enable "Add Python to PATH".
  pause
  exit /b 1
)

echo Installing/updating PyInstaller...
py -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo Failed to install PyInstaller.
  pause
  exit /b 1
)

echo.
echo Installing runtime requirements...
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Failed to install runtime requirements.
  pause
  exit /b 1
)

echo.
echo Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Building executable...
py -m PyInstaller --clean --noconfirm StoneLightLauncher.spec
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

echo.
echo Copying writable runtime files next to the exe...
copy /Y "config.json" "dist\StoneLight Launcher\config.json" >nul
copy /Y "requirements.txt" "dist\StoneLight Launcher\requirements.txt" >nul
copy /Y "README.md" "dist\StoneLight Launcher\README.md" >nul
copy /Y "SECURITY.md" "dist\StoneLight Launcher\SECURITY.md" >nul
copy /Y "MODS_FOUND.md" "dist\StoneLight Launcher\MODS_FOUND.md" >nul

if exist "docs" (
  robocopy "docs" "dist\StoneLight Launcher\docs" /E >nul
)
if exist "assets" (
  robocopy "assets" "dist\StoneLight Launcher\assets" /E >nul
)

echo.
echo Done!
echo.
echo Executable:
echo   dist\StoneLight Launcher\StoneLight Launcher.exe
echo.
echo You can zip the whole "dist\StoneLight Launcher" folder and publish it in GitHub Releases.
echo Recommended asset name: StoneLightLauncher_v0_5_62_Windows.zip
echo.
pause
