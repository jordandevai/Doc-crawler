@echo off
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%venv"
set "REQUIREMENTS_FILE=%PROJECT_DIR%requirements.txt"
set "MAIN_SCRIPT=%PROJECT_DIR%main.py"

echo 🚀 Doc-Crawler Launcher
echo ========================

cd /d "%PROJECT_DIR%"

if not exist "%VENV_DIR%" (
    echo 📦 Creating virtual environment...
    python -m venv "%VENV_DIR%"
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment exists
)

echo 🔧 Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

if not exist "%VENV_DIR%\requirements_installed.flag" (
    echo 📋 Installing requirements...
    python -m pip install --upgrade pip
    pip install -r "%REQUIREMENTS_FILE%"
    echo. > "%VENV_DIR%\requirements_installed.flag"
    echo ✅ Requirements installed
) else (
    echo ✅ Requirements already installed
)

echo 🏃 Launching Doc-Crawler...
echo.

python "%MAIN_SCRIPT%"

pause