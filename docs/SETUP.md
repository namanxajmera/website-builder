# ⚙️ AI Website Modernizer - Complete Setup Guide

## Overview

This comprehensive setup guide walks you through installing and configuring the AI Website Modernizer on your system. Follow these steps to get the application running locally for website transformation.

## 📋 System Requirements

### Operating System Support
- **macOS**: 10.14+ (Mojave or later)
- **Linux**: Ubuntu 18.04+, CentOS 7+, or equivalent
- **Windows**: 10+ (with WSL recommended for best compatibility)

### Software Prerequisites
- **Python**: 3.9 or higher ([Download here](https://www.python.org/downloads/))
- **Chrome Browser**: Latest stable version
- **Git**: For repository cloning
- **Terminal/Command Prompt**: For command execution

### Hardware Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Stable internet connection for crawling and AI API calls

## 🔧 Installation Steps

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone <repository-url>
cd ai-website-modernizer

# Verify you're in the correct directory
ls -la
# Should show: crawl_site.py, dashboard.py, remake_site_with_ai.py, etc.
```

### Step 2: Python Environment Setup

#### Option A: Using venv (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Verify activation (should show venv path)
which python
```

#### Option B: Using conda

```bash
# Create conda environment
conda create -n website-modernizer python=3.9
conda activate website-modernizer
```

### Step 3: Install Dependencies

The project uses pinned dependencies for reproducible builds (see [`requirements.txt`](./requirements.txt)):

```bash
# Install all required packages
pip install -r requirements.txt

# Verify key packages are installed
pip list | grep -E "(selenium|streamlit|google-genai|beautifulsoup4)"
```

**Key Dependencies Installed**:
- `selenium==4.34.0` - Web crawling automation
- `streamlit==1.46.1` - Dashboard UI framework  
- `google-genai==1.23.0` - Gemini AI integration
- `beautifulsoup4==4.13.4` - HTML parsing

### Step 4: ChromeDriver Setup

#### Automatic Installation (Recommended)

ChromeDriver is automatically managed by Selenium 4.x, but you can verify Chrome browser is installed:

```bash
# Check Chrome installation
# macOS:
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version

# Linux:
google-chrome --version

# Windows:
"C:\Program Files\Google\Chrome\Application\chrome.exe" --version
```

#### Manual ChromeDriver Installation (If Needed)

If you encounter WebDriver issues, manually install ChromeDriver:

```bash
# macOS with Homebrew
brew install chromedriver

# Linux (Ubuntu/Debian)
sudo apt-get install chromium-driver

# Or download directly from: https://chromedriver.chromium.org/
```

**Verification**: The crawler's [`setup_driver()`](./crawl_site.py#L68-L85) function will test ChromeDriver initialization.

### Step 5: Google Gemini API Configuration

#### Get Your API Key

1. Visit [Google AI Studio](https://ai.google.dev/gemini-api/docs/quickstart?lang=python)
2. Sign in with your Google account
3. Create a new API key
4. Copy the API key for configuration

#### Set Environment Variable

**Temporary Setup (Session Only)**:
```bash
export GOOGLE_GEMINI_API_KEY=your-api-key-here
```

**Permanent Setup (Recommended)**:

```bash
# macOS/Linux - Add to shell profile
echo 'export GOOGLE_GEMINI_API_KEY=your-api-key-here' >> ~/.bashrc
echo 'export GOOGLE_GEMINI_API_KEY=your-api-key-here' >> ~/.zshrc

# Reload shell configuration
source ~/.bashrc  # or source ~/.zshrc

# Windows - Set user environment variable
setx GOOGLE_GEMINI_API_KEY "your-api-key-here"
```

**Verification**: The API key loading is handled by [`load_gemini_api_key()`](./remake_site_with_ai.py#L20-L30):

```bash
# Test API key configuration
python -c "import os; print('API key configured:' if os.getenv('GOOGLE_GEMINI_API_KEY') else 'API key missing')"
```

## 🚀 Launch Options

### Option 1: One-Click Startup Scripts (Recommended)

The project includes automated startup scripts that handle environment setup and launch:

#### macOS/Linux
```bash
# Make script executable
chmod +x start.sh

# Launch dashboard
./start.sh
```

#### Windows
```bash
# Run startup script
start.bat
```

**What the startup scripts do**:
1. Check and create virtual environment if needed
2. Activate virtual environment
3. Install/update dependencies from [`requirements.txt`](./requirements.txt)
4. Launch Streamlit dashboard via [`dashboard.py`](./dashboard.py)
5. Open browser to http://localhost:8501

### Option 2: Manual Dashboard Launch

If you prefer manual control or need debugging:

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Launch Streamlit dashboard
streamlit run dashboard.py

# Alternative: specify port and configuration
streamlit run dashboard.py --server.port 8501 --server.address localhost
```

### Option 3: Command Line Interface

For advanced users or automation, use the CLI directly:

```bash
# Step 1: Crawl a website
python crawl_site.py https://example.com --max_pages 10 --depth 2

# Step 2: Generate AI-modernized version
python remake_site_with_ai.py example_com --model gemini-2.5-flash-preview-05-20

# The output will be in example_com_ai/ directory
```

## 🔍 Verification & Testing

### Test Installation

1. **Verify Python Environment**:
   ```bash
   python --version  # Should show 3.9+
   pip list | wc -l  # Should show 50+ packages
   ```

2. **Test ChromeDriver Setup**:
   ```bash
   python -c "
   from selenium import webdriver
   from selenium.webdriver.chrome.options import Options
   options = Options()
   options.add_argument('--headless')
   driver = webdriver.Chrome(options=options)
   print('ChromeDriver working!')
   driver.quit()
   "
   ```

3. **Test API Key Configuration**:
   ```bash
   python -c "
   import os
   api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
   print(f'API key configured: {bool(api_key)}')
   if api_key: print(f'Key preview: {api_key[:10]}...')
   "
   ```

4. **Test Streamlit Launch**:
   ```bash
   streamlit hello
   # Should open browser to Streamlit demo
   # Press Ctrl+C to stop
   ```

### Run Sample Transformation

Test the complete pipeline with a simple website:

```bash
# Launch dashboard
streamlit run dashboard.py

# In the web interface:
# 1. Enter URL: https://example.com
# 2. Click "Modernize Website!"
# 3. Monitor progress in real-time
# 4. Preview generated site when complete
```

## ⚙️ Configuration Options

### Dashboard Configuration

Streamlit configuration via [`dashboard.py:15-20`](./dashboard.py#L15-L20):

```python
st.set_page_config(
    page_title="AI Website Modernizer",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed"
)
```

### Crawling Configuration

Default settings in [`crawl_site.py:19-20`](./crawl_site.py#L19-L20):

```python
DEFAULT_MAX_PAGES = 20          # Maximum pages to crawl
DEFAULT_CRAWL_DEPTH = 2         # Maximum crawling depth
```

Override via command line:
```bash
python crawl_site.py https://example.com --max_pages 50 --depth 3
```

### AI Model Configuration

Available models in [`remake_site_with_ai.py:170-171`](./remake_site_with_ai.py#L170-L171):

- **gemini-2.5-flash-preview-05-20** (default): Fast processing, good for most sites
- **gemini-1.5-pro-latest**: Comprehensive analysis, better for complex sites

```bash
# Use specific model
python remake_site_with_ai.py site_folder --model gemini-1.5-pro-latest --temperature 0.7
```

## 🐛 Common Setup Issues

### ChromeDriver Issues

**Problem**: "ChromeDriver not found" or "WebDriver not available"

**Solutions**:
```bash
# Check Chrome installation
google-chrome --version

# Update Chrome to latest version
# macOS: Chrome menu > About Google Chrome
# Linux: sudo apt update && sudo apt upgrade google-chrome-stable
# Windows: Chrome menu > Help > About Google Chrome

# Verify Selenium can find ChromeDriver
python -c "from selenium import webdriver; print('OK')"
```

### Python Version Issues

**Problem**: "Python version 3.9+ required"

**Solutions**:
```bash
# Check current version
python --version

# Install newer Python
# macOS: brew install python@3.11
# Linux: sudo apt install python3.11
# Windows: Download from python.org

# Create venv with specific version
python3.11 -m venv venv
```

### Dependency Conflicts

**Problem**: Package installation failures or conflicts

**Solutions**:
```bash
# Clean installation
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# For development with dependency management
pip install pip-tools
pip-compile requirements.in  # Update requirements.txt
```

### API Key Issues

**Problem**: "API key not found" or "Authentication failed"

**Solutions**:
```bash
# Verify environment variable
echo $GOOGLE_GEMINI_API_KEY

# Re-export if needed
export GOOGLE_GEMINI_API_KEY=your-actual-api-key

# Test API access
python -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
print('API connection successful')
"
```

### Port Conflicts

**Problem**: "Port 8501 already in use"

**Solutions**:
```bash
# Find process using port
lsof -i :8501

# Kill existing Streamlit process
pkill -f streamlit

# Or use different port
streamlit run dashboard.py --server.port 8502
```

## 🔧 Development Setup

### For Contributors

```bash
# Clone repository
git clone <repository-url>
cd ai-website-modernizer

# Create development environment
python3 -m venv dev-env
source dev-env/bin/activate

# Install dependencies with development tools
pip install -r requirements.txt
pip install pip-tools  # For dependency management

# Make changes and test
python crawl_site.py --help
python remake_site_with_ai.py --help
streamlit run dashboard.py
```

### Dependency Management

For updating dependencies, edit [`requirements.in`](./requirements.in) and regenerate:

```bash
# Edit requirements.in with new packages
pip-compile requirements.in

# Install updated requirements
pip install -r requirements.txt
```

## 📁 Directory Structure After Setup

```
ai-website-modernizer/
├── venv/                       # Virtual environment
├── crawl_site.py              # Web crawler module
├── remake_site_with_ai.py     # AI processing module
├── dashboard.py               # Streamlit dashboard
├── prompts/
│   └── rebuild_prompt.txt     # AI prompt template
├── requirements.txt           # Python dependencies
├── requirements.in            # Dependency source file
├── start.sh                   # macOS/Linux startup script
├── start.bat                  # Windows startup script
└── README.md                  # Project documentation

Generated during usage:
├── example_com/               # Crawled site data
│   ├── home/
│   ├── about/
│   └── crawl_manifest.json
└── example_com_ai/            # AI-generated modern site
    ├── global_styles.css
    ├── index.html
    └── about.html
```

## 🎯 Next Steps

After successful setup:

1. **Launch Dashboard**: `streamlit run dashboard.py`
2. **Test with Simple Site**: Try https://example.com first
3. **Explore Features**: Use different AI models and settings
4. **Read Documentation**: Check [`README.md`](./README.md) for usage details
5. **Join Community**: Report issues and contribute improvements

## 📞 Getting Help

If you encounter issues during setup:

1. **Check logs**: Enable verbose output with `export DEBUG_MODE=1`
2. **Verify prerequisites**: Ensure all system requirements are met
3. **Review error messages**: Most errors include actionable solutions
4. **Check documentation**: Review function docstrings and inline comments in source files
5. **Report bugs**: Create GitHub issue with setup details and error logs

---

*Setup complete! You're ready to transform websites with AI-powered modernization.*