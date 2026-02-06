@echo off
title AI Operations Assistant - Setup

echo ================================================================================
echo               AI OPERATIONS ASSISTANT - WINDOWS SETUP
echo ================================================================================
echo.

REM Check Python installation
echo [*] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% found.
echo.

REM Create virtual environment
echo [*] Creating virtual environment...
if exist "venv" (
    echo [!] Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
)
echo.

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated.
echo.

REM Install dependencies
echo [*] Installing dependencies (this may take 2-3 minutes)...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo.
echo [OK] All dependencies installed successfully!
echo.

REM Check .env file
if exist ".env" (
    echo [OK] Environment file (.env) found.
) else (
    echo [!] Creating .env file from template...
    copy .env.example .env
    echo [OK] .env file created. Please add your API key.
)
echo.

echo ================================================================================
echo                        SETUP COMPLETE!
echo ================================================================================
echo.
echo To run the application:
echo.
echo   Option 1: Double-click "run_app.bat"
echo.
echo   Option 2: Open Command Prompt here and run:
echo             venv\Scripts\activate
echo             python main.py --api --port 8000
echo.
echo Then open your browser to: http://localhost:8000
echo.
echo ================================================================================
echo.

pause
