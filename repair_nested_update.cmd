@echo off
chcp 65001 >nul
title Repair nested StoneLight Launcher update

echo.
echo ========================================
echo   Repair nested StoneLight Launcher update
echo ========================================
echo.
echo This fixes the case where an update created:
echo   .\StoneLight Launcher\
echo inside the current launcher folder.
echo.

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "NESTED=%ROOT%\StoneLight Launcher"

if not exist "%NESTED%\StoneLight Launcher.exe" (
  echo Nested updated launcher was not found:
  echo   %NESTED%\StoneLight Launcher.exe
  echo.
  echo Nothing to repair.
  pause
  exit /b 1
)

echo Current launcher folder:
echo   %ROOT%
echo.
echo Nested updated folder:
echo   %NESTED%
echo.
echo Copying nested update one level up...
echo User data will be preserved.
echo.

robocopy "%NESTED%" "%ROOT%" /E /XD ".git" "data" "__pycache__" ".venv" "venv" "env" /XF "accounts.json" "user_settings.json" "instances.json" "*.log" "*.zip" "apply_launcher_update.cmd" "repair_nested_update.cmd"
set "RC=%ERRORLEVEL%"

if %RC% GEQ 8 (
  echo.
  echo Repair failed. Robocopy code: %RC%
  pause
  exit /b %RC%
)

echo.
echo Removing nested folder...
rmdir /s /q "%NESTED%"

echo.
echo Repair complete.
echo.
if exist "%ROOT%\StoneLight Launcher.exe" (
  start "" "%ROOT%\StoneLight Launcher.exe"
)
exit /b 0
