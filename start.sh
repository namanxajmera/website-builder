#!/bin/bash

# 🚀 AI Website Modernizer - One-Click Startup Script
# This script automatically sets up the environment and launches the dashboard

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${CYAN}🚀 AI Website Modernizer Startup${NC}"
echo -e "${CYAN}=================================${NC}"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
    echo -e "${YELLOW}Please install Python 3.9+ and try again.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
MIN_VERSION="3.9"
if [[ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]]; then
    echo -e "${RED}❌ Python 3.9+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $PYTHON_VERSION detected${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if requirements are installed
if [ ! -f "venv/.requirements_installed" ]; then
    echo -e "${BLUE}📋 Installing dependencies...${NC}"
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1
    touch venv/.requirements_installed
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi

# Check for API key
if [ -z "$GOOGLE_GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_GEMINI_API_KEY not set${NC}"
    echo -e "${CYAN}To use the AI features, set your API key:${NC}"
    echo -e "${CYAN}export GOOGLE_GEMINI_API_KEY=your-api-key-here${NC}"
    echo -e "${CYAN}Get your API key: https://ai.google.dev/gemini-api/docs/quickstart${NC}"
    echo
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ API key configured${NC}"
fi

# Check if Chrome/Chromium is available for Selenium
if ! command -v google-chrome &> /dev/null && ! command -v chromium &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    echo -e "${YELLOW}⚠️  Chrome browser not detected${NC}"
    echo -e "${CYAN}For web crawling, install Google Chrome or Chromium${NC}"
    echo
fi

# Launch the dashboard
echo -e "${BLUE}🌐 Starting dashboard...${NC}"
echo -e "${CYAN}Dashboard will open at: http://localhost:8501${NC}"
echo -e "${CYAN}Press Ctrl+C to stop${NC}"
echo

# Start Streamlit with optimized settings
streamlit run dashboard.py \
    --server.address localhost \
    --server.port 8501 \
    --browser.gatherUsageStats false \
    --server.headless true \
    --server.fileWatcherType none \
    2>/dev/null