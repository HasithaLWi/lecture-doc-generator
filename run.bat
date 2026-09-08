@echo off
REM ==============================================================================
REM Lecture Document Generator - Local Runner
REM Automatically invokes its own self-contained virtual environment
REM ==============================================================================

cd /d "%~dp0"

IF EXIST "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" main.py %*
) ELSE (
    python main.py %*
)

pause
