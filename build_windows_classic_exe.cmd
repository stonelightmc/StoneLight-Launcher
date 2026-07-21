@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Build StoneLight Launcher Classic EXE

echo.
echo ========================================
echo   StoneLight Launcher Classic EXE Builder
echo ========================================
echo.
echo This script builds the old CustomTkinter interface.
echo For the current Web UI build, use:
echo   build_windows_exe.cmd
echo.

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
      pause
      exit /b 1
    )
    set "PYTHON=python"
  )
)

%PYTHON% -m pip install --upgrade pyinstaller
if errorlevel 1 pause & exit /b 1

%PYTHON% -m pip install -r requirements.txt
if errorlevel 1 pause & exit /b 1

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

%PYTHON% -m PyInstaller --clean --noconfirm StoneLightLauncher.spec
if errorlevel 1 pause & exit /b 1

echo.
echo Classic build complete:
echo   dist\StoneLight Launcher\StoneLight Launcher.exe
echo.
pause
