@echo off
title FindIt Frontend - React/Vite Dev Server (Port 5173)
color 0B

echo.
echo  =========================================
echo   FindIt - Smart Lost ^& Found Platform
echo   Frontend Dev Server (React / Vite)
echo  =========================================
echo.
echo  Student  : Druva Kumar B  (ENG25AD0110)
echo  Branch   : AI^&DS  Section B  Roll 39
echo  Institute: Dayananda Sagar University
echo  =========================================
echo.
echo  Open in browser: http://localhost:5173
echo  (Make sure the backend is running first!)
echo.

set "NODE=%~dp0.tools\nodejs\node.exe"
set "NPM_CLI=%~dp0.tools\nodejs\node_modules\npm\bin\npm-cli.js"
if exist "%NODE%" if exist "%NPM_CLI%" goto bundled_node

where node >nul 2>nul
if errorlevel 1 (
    echo ERROR: Node.js was not found. Install Node.js or restore .tools\nodejs.
    pause
    exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
    echo ERROR: npm was not found.
    pause
    exit /b 1
)

cd /d "%~dp0frontend"
echo Starting Vite dev server...
echo.

npm run dev
goto frontend_done

:bundled_node
cd /d "%~dp0frontend"
echo Starting Vite dev server...
echo.
"%NODE%" "%NPM_CLI%" run dev

:frontend_done

pause
