@echo off
title FindIt Backend - Flask API (Port 5000)
color 0A

echo.
echo  =========================================
echo   FindIt - Smart Lost ^& Found Platform
echo   Backend Server (Flask / Python)
echo  =========================================
echo.
echo  Student  : Druva Kumar B  (ENG25AD0110)
echo  Branch   : AI^&DS  Section B  Roll 39
echo  Institute: Dayananda Sagar University
echo  =========================================
echo.

set "PYTHON=%~dp0.tools\venv\Scripts\python.exe"
if not exist "%PYTHON%" set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
    echo ERROR: Python environment was not found.
    echo Create .venv or install the bundled .tools environment.
    pause
    exit /b 1
)

cd /d "%~dp0backend"
echo Starting Flask development server on http://localhost:5000
echo.
echo  Press Ctrl+C to stop the server.
echo.

"%PYTHON%" run.py

pause
