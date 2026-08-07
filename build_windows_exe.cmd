@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Build StoneLight Launcher EXE

echo.
echo ========================================
echo   StoneLight Launcher Web UI EXE Builder
echo ========================================
echo.
echo This script creates:
echo   dist\StoneLight Launcher\StoneLight Launcher.exe
echo.
echo Current main UI:
echo   StoneLightLauncherWeb.pyw
echo.
echo Spec:
echo   StoneLightLauncherWeb.spec
echo.

if not exist "StoneLightLauncherWeb.spec" (
  echo ERROR: StoneLightLauncherWeb.spec was not found.
  pause
  exit /b 1
)

if exist ".venv\Scripts\python.exe" (
  set "PYTHON=.venv\Scripts\python.exe"
) else (
  where py >nul 2>nul
  if not errorlevel 1 (
    set "PYTHON=py"
  ) else (
    where python >nul 2>nul
    if errorlevel 1 (
      echo Python was not found.
      echo Install Python 3.12+ or run setup.cmd first.
      pause
      exit /b 1
    )
    set "PYTHON=python"
  )
)

echo Python command:
echo   %PYTHON%
echo.

echo Installing/updating PyInstaller...
%PYTHON% -m pip install --upgrade pyinstaller
if errorlevel 1 (
  echo Failed to install PyInstaller.
  pause
  exit /b 1
)

echo.
echo Installing runtime requirements...
%PYTHON% -m pip install -r requirements.txt
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
echo Building Web UI executable...
%PYTHON% -m PyInstaller --clean --noconfirm StoneLightLauncherWeb.spec
if errorlevel 1 (
  echo Build failed.
  pause
  exit /b 1
)

if not exist "dist\StoneLight Launcher\StoneLight Launcher.exe" (
  echo Build finished, but the expected exe was not found:
  echo   dist\StoneLight Launcher\StoneLight Launcher.exe
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
if exist "web_ui" (
  robocopy "web_ui" "dist\StoneLight Launcher\web_ui" /E >nul
)

echo.
echo Creating release archive...
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Test-Path 'StoneLightLauncher_v0_6_71_Windows.zip') { Remove-Item 'StoneLightLauncher_v0_6_71_Windows.zip' -Force }; Compress-Archive -Path 'dist\StoneLight Launcher\*' -DestinationPath 'StoneLightLauncher_v0_6_71_Windows.zip'"
if errorlevel 1 (
  echo Archive creation failed, but exe build is complete.
  echo Folder:
  echo   dist\StoneLight Launcher
  pause
  exit /b 0
)

echo.
echo Done!
echo.
echo Executable:
echo   dist\StoneLight Launcher\StoneLight Launcher.exe
echo.
echo Release archive:
echo   StoneLightLauncher_v0_6_71_Windows.zip
echo.
pause
