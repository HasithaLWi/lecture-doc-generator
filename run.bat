@echo off
REM ==============================================================================
REM Lecture Document Generator - Smart Launcher
REM Automatically ensures virtual environment and dependencies are installed!
REM ==============================================================================

cd /d "%~dp0"

REM Step 1: Ensure virtual environment exists
IF NOT EXIST "venv\Scripts\python.exe" (
    echo ==============================================================================
    echo [Setup] Virtual environment (venv) not found. Creating venv now...
    echo ==============================================================================
    python -m venv venv
    IF ERRORLEVEL 1 (
        echo [Error] Failed to create virtual environment. Please ensure Python is installed and added to PATH.
        pause
        exit /b 1
    )
    echo [Setup] Installing required dependencies into venv...
    "venv\Scripts\python.exe" -m pip install --upgrade pip
    "venv\Scripts\python.exe" -m pip install -r requirements.txt
    IF ERRORLEVEL 1 (
        echo [Error] Failed to install dependencies from requirements.txt.
        pause
        exit /b 1
    )
    echo [Setup] Setup complete!
    echo.
)

REM Step 2: Launch App (GUI by default, CLI if arguments are passed)
IF "%~1"=="" (
    "venv\Scripts\python.exe" gui.py
) ELSE (
    "venv\Scripts\python.exe" main.py %*
    pause
)
