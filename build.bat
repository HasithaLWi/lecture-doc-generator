@echo off
REM ==============================================================================
REM Lecture Document Generator - Executable Builder
REM Compiles standalone LectureDocGenerator.exe using PyInstaller
REM ==============================================================================

cd /d "%~dp0"

echo ==============================================================================
echo [Build] Starting standalone .exe build process...
echo ==============================================================================

IF EXIST "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" build_exe.py
) ELSE (
    python build_exe.py
)

pause
