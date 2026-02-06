@echo off
title AI Operations Assistant

echo ================================================================================
echo                      AI OPERATIONS ASSISTANT
echo ================================================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [!] Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Is Python installed?
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
    echo.
)

REM Activate virtual environment
echo [*] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [!] Dependencies not installed. Installing now...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed.
    echo.
)

echo.
echo Choose how to run the application:
echo.
echo   1. Web UI Mode (opens browser automatically)
echo   2. Interactive CLI Mode
echo   3. Exit
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" (
    echo.
    echo [*] Starting Web UI on http://localhost:8000
    echo [*] Opening browser...
    start http://localhost:8000
    echo.
    echo Press Ctrl+C to stop the server.
    echo.
    python main.py --api --port 8000
) else if "%choice%"=="2" (
    echo.
    echo [*] Starting Interactive CLI Mode...
    echo.
    python main.py
) else if "%choice%"=="3" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid choice. Please run again.
    pause
    exit /b 1
)

pause
