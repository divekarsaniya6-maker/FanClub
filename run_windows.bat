@echo off
title FanClub - Professional Football Ground Booking Platform
color 0A

echo =====================================================================
echo    ⚽ FANCLUB – PROFESSIONAL FOOTBALL GROUND BOOKING WEBSITE
echo    "YOUR GAME. YOUR CLUB."
echo =====================================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from python.org and check "Add to PATH".
    pause
    exit /b 1
)

:: Create virtual environment if needed
if not exist "venv" (
    echo [*] Setting up Python virtual environment (venv)...
    python -m venv venv
)

:: Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat 2>nul || (
    echo [!] Using active Python environment.
)

:: Install required packages
echo [*] Installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet

:: Initialize Database schema and venue inventory
echo [*] Initializing database and verified turf inventory...
python scripts\init_db.py

echo.
echo =====================================================================
echo    🚀 FANCLUB READY FOR MATCHDAY!
echo    URL: http://127.0.0.1:5000
echo    To create an administrator, run: python scripts\create_admin.py
echo =====================================================================
echo.

:: Launch Default Browser after 2 seconds
start "" http://127.0.0.1:5000

:: Start Flask Application Server
python app.py
pause
