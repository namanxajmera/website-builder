@echo off
REM 🚀 AI Website Modernizer - One-Click Startup Script (Windows)
REM This script automatically sets up the environment and launches the dashboard

setlocal enabledelayedexpansion

echo 🚀 AI Website Modernizer Startup
echo =================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is required but not installed.
    echo Please install Python 3.9+ from https://python.org and try again.
    pause
    exit /b 1
)

echo ✅ Python detected

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
if not exist "venv\.requirements_installed" (
    echo 📋 Installing dependencies...
    pip install --upgrade pip >nul 2>&1
    pip install -r requirements.txt >nul 2>&1
    echo. > venv\.requirements_installed
    echo ✅ Dependencies installed
) else (
    echo ✅ Dependencies already installed
)

REM Check for API key
if "%GOOGLE_GEMINI_API_KEY%"=="" (
    echo ⚠️  GOOGLE_GEMINI_API_KEY not set
    echo To use the AI features, set your API key:
    echo set GOOGLE_GEMINI_API_KEY=your-api-key-here
    echo Get your API key: https://ai.google.dev/gemini-api/docs/quickstart
    echo.
    set /p continue="Continue anyway? (y/N): "
    if not "!continue!"=="y" if not "!continue!"=="Y" exit /b 1
) else (
    echo ✅ API key configured
)

REM Launch the dashboard
echo 🌐 Starting dashboard...
echo Dashboard will open at: http://localhost:8501
echo Press Ctrl+C to stop
echo.

REM Start Streamlit
streamlit run dashboard.py --server.address localhost --server.port 8501 --browser.gatherUsageStats false --server.headless true --server.fileWatcherType none 2>nul