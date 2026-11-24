@echo off
title FindIt - Deploy to Vercel
color 0B

echo.
echo  =========================================
echo   FindIt - Smart Lost ^& Found Platform
echo   Vercel Deployment Assistant
echo  =========================================
echo.
echo  Student  : Druva Kumar B  (ENG25AD0110)
echo  Institute: Dayananda Sagar University
echo  =========================================
echo.

cd /d "%~dp0"

echo [1/3] Building frontend production bundle...
cd frontend
call "%~dp0.tools\nodejs\node.exe" "%~dp0.tools\nodejs\node_modules\npm\bin\npm-cli.js" run build
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed. Please fix build errors before deploying.
    pause
    exit /b %errorlevel%
)
cd ..

echo.
echo [2/3] Preparing Vercel deployment...
echo.
echo If this is your first time:
echo   - Vercel will ask you to log in (browser will open or enter your email).
echo   - Follow the simple prompts:
echo       * Set up and deploy? [Y]
echo       * Which scope? (Select your account)
echo       * Link to existing project? [N]
echo       * Project name? [findit-lost-and-found] (or press Enter)
echo       * In which directory is your code located? [./] (press Enter)
echo.
echo [3/3] Launching Vercel CLI...
echo.

"%~dp0.tools\nodejs\node.exe" "%~dp0.tools\nodejs\node_modules\npm\bin\npx-cli.js" --yes vercel

echo.
echo =========================================
echo  Deployment command finished!
echo =========================================
echo.
pause
