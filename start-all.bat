@echo off
title FindIt Platform - Launcher
color 0E

echo.
echo  =========================================
echo   FindIt - Smart Lost ^& Found Platform
echo   Full-Stack Launcher
echo  =========================================
echo.
echo  Student  : Druva Kumar B  (ENG25AD0110)
echo  Branch   : AI^&DS  Section B  Roll 39
echo  Institute: Dayananda Sagar University
echo  =========================================
echo.
echo  This will open TWO terminal windows:
echo    1. Backend  -^> http://localhost:5000
echo    2. Frontend -^> http://localhost:5173
echo.
echo  Wait for both servers to start, then
echo  visit: http://localhost:5173
echo.
pause

echo Starting backend server...
start "FindIt Backend" cmd /c "%~dp0start-backend.bat"

timeout /t 3 /nobreak >nul

echo Starting frontend server...
start "FindIt Frontend" cmd /c "%~dp0start-frontend.bat"

echo.
echo  Both servers starting up. 
echo  Open http://localhost:5173 in your browser.
echo.
pause
