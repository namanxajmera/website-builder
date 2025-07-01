# 🚀 AI Website Modernizer

**Transform any website into a modern, responsive, and SEO-optimized experience using Google Gemini AI.**

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)

## 🎯 Overview

AI Website Modernizer is an intelligent web transformation tool that analyzes existing websites and automatically rebuilds them with modern design principles, improved user experience, and optimized performance. Using advanced AI capabilities powered by Google Gemini, it creates cohesive, responsive websites that maintain brand identity while dramatically improving functionality.

### 🏗️ Core Components

- **Web Crawler** ([`crawl_site.py`](./crawl_site.py)) - Selenium-based content extraction with SSRF protection
- **AI Processor** ([`remake_site_with_ai.py`](./remake_site_with_ai.py)) - Gemini AI integration for holistic site redesign  
- **Dashboard Interface** ([`dashboard.py`](./dashboard.py)) - Streamlit UI for seamless user experience
- **Prompt Engineering** ([`prompts/rebuild_prompt.txt`](./prompts/rebuild_prompt.txt)) - Sophisticated AI instructions for site generation

---

## ✨ Key Features

### 🤖 **Intelligent Website Analysis**
- **Smart Content Extraction**: Automatically crawls and analyzes website structure using [`crawl_site.py:get_page_content()`](./crawl_site.py#L99-L157)
- **Comprehensive Data Collection**: Captures HTML, CSS, images, and copy with configurable depth and page limits
- **SSRF Protection**: Enhanced security with [`is_safe_url()`](./crawl_site.py#L29-L66) validation
- **Content Understanding**: AI processes all page data simultaneously for holistic redesign approach

### 🎨 **AI-Powered Modernization**
- **Holistic Redesign**: Google Gemini AI analyzes entire site structure via [`gemini_generate_entire_site()`](./remake_site_with_ai.py#L32-L165)
- **Mobile-First Approach**: Automatically optimizes for responsive design and mobile user experience
- **SEO Optimization**: Implements modern SEO best practices and performance improvements
- **Brand Consistency**: Maintains brand identity while upgrading design language and user experience

### 🔧 **Technical Excellence**
- **Structured Output**: Generates clean, maintainable code with global stylesheets and organized HTML
- **Scalable Architecture**: Three-stage pipeline (Crawl → AI Processing → Generation) for reliable results
- **Security-First**: Secure API key handling via [`load_gemini_api_key()`](./remake_site_with_ai.py#L20-L30) and path traversal protection
- **Error Resilience**: Comprehensive timeout handling and graceful error recovery

### 📊 **User-Friendly Interface**
- **Interactive Dashboard**: Streamlit-powered UI with [`run_full_process()`](./dashboard.py#L184-L272)
- **Real-Time Monitoring**: Live progress tracking via [`run_subprocess_and_log()`](./dashboard.py#L139-L182)
- **Preview Capability**: Instant preview with [`display_preview()`](./dashboard.py#L113-L136)
- **Process Transparency**: Clear status indicators and detailed feedback

## 🔄 How It Works

```mermaid
graph LR
    A[Input Website URL] --> B[Web Crawling]
    B --> C[Content Extraction]
    C --> D[AI Analysis]
    D --> E[Design Generation]
    E --> F[Modern Website Output]
```

1. **🕷️ Web Crawling**: [`crawl_site.py:main()`](./crawl_site.py#L269-L429) discovers and crawls website pages using Selenium WebDriver
2. **📝 Content Extraction**: [`save_page_data()`](./crawl_site.py#L217-L267) structures HTML, CSS, images, and text content
3. **🧠 AI Analysis**: [`remake_site_with_ai.py`](./remake_site_with_ai.py) processes all content with Google Gemini for comprehensive understanding
4. **🎨 Design Generation**: AI creates modern, responsive design with improved UX and SEO
5. **📦 Output Generation**: Produces clean, organized website files ready for deployment

---

## 📋 Prerequisites

- Python 3.9+ (see [`requirements.txt`](./requirements.txt))
- Chrome browser and ChromeDriver (for Selenium WebDriver in [`crawl_site.py:setup_driver()`](./crawl_site.py#L68-L85))
- Google Gemini API key ([Get one here](https://ai.google.dev/gemini-api/docs/quickstart?lang=python))

## 🚀 Quick Start

### 1. **Clone & Setup**
```bash
git clone <repository-url>
cd ai-website-modernizer
```

### 2. **Environment Setup**
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install pinned dependencies for reproducible builds
pip install -r requirements.txt

# For development: install pip-tools to manage dependencies
pip install pip-tools

# To update dependencies: edit requirements.in, then run:
# pip-compile requirements.in
```

### 3. **API Configuration**
```bash
# Set your Google Gemini API key
export GOOGLE_GEMINI_API_KEY=your-api-key-here

# For permanent setup (recommended)
echo 'export GOOGLE_GEMINI_API_KEY=your-api-key-here' >> ~/.bashrc
source ~/.bashrc
```

> 🔑 **Get your API key**: [Google AI Studio](https://ai.google.dev/gemini-api/docs/quickstart?lang=python)

### 4. **Launch Dashboard**

**🚀 One-Click Startup (Recommended)**
```bash
# macOS/Linux
./start.sh

# Windows
start.bat
```

**Manual Launch**
```bash
streamlit run dashboard.py
```

Open your browser to `http://localhost:8501` and start transforming websites! 🎉

> The startup scripts automatically handle virtual environment creation, dependency installation, and dashboard launch.

---

## 💻 Usage Options

### 🎯 **Recommended: Interactive Dashboard**
```bash
streamlit run dashboard.py
```
- **User-friendly interface** with real-time progress tracking via [`dashboard.py`](./dashboard.py)
- **One-click transformation** from URL input to modernized website
- **Live preview** of transformed pages with [`modify_html_for_preview()`](./dashboard.py#L81-L111)
- **Detailed logging** and status monitoring

### 🔧 **Advanced: Command Line Interface**

#### Crawl Website
```bash
python crawl_site.py https://example.com --max_pages 10 --depth 2
```

#### AI Transformation
```bash
python remake_site_with_ai.py example.com --model gemini-2.5-flash-preview-05-20
```

**Available Models:**
- `gemini-2.5-flash-preview-05-20` (default, fast)
- `gemini-1.5-pro-latest` (comprehensive, large context)

## 📁 Output Structure

```
📦 example.com/                    # Original crawled data
 ┣ 📂 home/
 ┃ ┣ 📄 url.txt                   # Page URL
 ┃ ┣ 📄 page.html                 # Original HTML
 ┃ ┣ 📄 copy.txt                  # Extracted text content
 ┃ ┣ 📄 images.txt                # Image URLs
 ┃ ┗ 📄 css.txt                   # CSS styles
 ┣ 📂 about/
 ┃ ┗ 📄 ...
 ┗ 📄 crawl_manifest.json         # Crawl metadata

📦 example.com_ai/                 # 🎨 AI-Enhanced Website
 ┣ 📄 global_styles.css           # Modern global stylesheet
 ┣ 📂 home/
 ┃ ┣ 📄 index.html                # ✨ Modernized HTML
 ┃ ┗ 📄 original_*.txt            # Reference files
 ┗ 📂 about/
   ┗ 📄 index.html
```

## 🏗️ Architecture

### **Three-Stage Pipeline**
```
🕷️ Crawl → 🧠 AI Processing → 📦 Generation
```

1. **Crawler Module** ([`crawl_site.py`](./crawl_site.py))
   - Selenium WebDriver with [`setup_driver()`](./crawl_site.py#L68-L85) for JavaScript-rendered sites
   - Structured content extraction via [`get_page_content()`](./crawl_site.py#L99-L157)
   - Configurable depth and page limits with [`DEFAULT_MAX_PAGES`](./crawl_site.py#L19) and [`DEFAULT_CRAWL_DEPTH`](./crawl_site.py#L20)

2. **AI Processing** ([`remake_site_with_ai.py`](./remake_site_with_ai.py))
   - Google Gemini integration with [`gemini_generate_entire_site()`](./remake_site_with_ai.py#L32-L165)
   - Holistic content analysis and design generation using [`prompts/rebuild_prompt.txt`](./prompts/rebuild_prompt.txt)
   - Enhanced path traversal protection with filename validation

3. **Dashboard Interface** ([`dashboard.py`](./dashboard.py))
   - Streamlit-powered user interface with [`st.set_page_config()`](./dashboard.py#L15-L20)
   - Real-time progress monitoring via [`update_step_status()`](./dashboard.py#L77-L78)
   - Manifest-based reliable inter-process communication with [`read_crawl_manifest()`](./dashboard.py#L61-L75)

## 🧠 AI & Technical Details

### **Prompt Engineering**
- **Holistic Analysis**: All crawled content processed simultaneously for cohesive design via [`prompts/rebuild_prompt.txt`](./prompts/rebuild_prompt.txt)
- **Design Principles**: Mobile-first responsiveness, SEO optimization, accessibility
- **Brand Preservation**: Maintains original brand identity while modernizing experience
- **Structured Output**: JSON-formatted response with global CSS and individual page HTML

### **Security & Reliability**
- **🔒 Secure API Handling**: Environment-based API key management via [`load_gemini_api_key()`](./remake_site_with_ai.py#L20-L30)
- **🛡️ Path Traversal Protection**: Enhanced filename validation in [`remake_site_with_ai.py:369-387`](./remake_site_with_ai.py#L369-L387)
- **⏱️ Timeout Management**: Prevents hanging on unresponsive pages with [`driver.set_page_load_timeout(30)`](./crawl_site.py#L78)
- **📊 Manifest Communication**: Reliable inter-script communication via [`crawl_manifest.json`](./crawl_site.py#L386-L412)

### **Performance Considerations**
- **Context Window**: Leverages large context windows (1M+ tokens) for comprehensive analysis
- **Scalable Architecture**: Modular design supports easy enhancement and maintenance
- **Error Resilience**: Graceful handling of network issues, API limits, and malformed content

---

## 🛠️ Troubleshooting

### **Common Issues & Solutions**

| Issue | Solution | Code Reference |
|-------|----------|---------------|
| **Missing Dependencies** | Run `pip install -r requirements.txt` in activated virtual environment | [`requirements.txt`](./requirements.txt) |
| **ChromeDriver Issues** | Ensure ChromeDriver matches Chrome version and is in PATH | [`setup_driver()`](./crawl_site.py#L68-L85) |
| **API Key Not Found** | Verify `GOOGLE_GEMINI_API_KEY` environment variable is set | [`load_gemini_api_key()`](./remake_site_with_ai.py#L20-L30) |
| **Timeout Errors** | Check internet connection; large sites may need multiple attempts | [`TimeoutException`](./crawl_site.py#L110-L112) |
| **JSON Parse Errors** | AI model occasionally returns malformed JSON; retry the process | [`json.JSONDecodeError`](./remake_site_with_ai.py#L144-L151) |
| **Memory Issues** | Use `gemini-2.5-flash-preview-05-20` for large sites instead of pro model | [`gemini_generate_entire_site()`](./remake_site_with_ai.py#L32) |

### **Debug Mode**
```bash
# Enable verbose logging
export DEBUG_MODE=1
streamlit run dashboard.py
```

### **Getting Help**
- 📖 **Documentation**: Check [`docs/`](./docs/) folder for comprehensive guides
- 🐛 **Issues**: Report bugs via GitHub Issues
- 💬 **Discussions**: Join community discussions for usage questions
- 📧 **Contact**: Reach out for enterprise or custom solutions

## 📚 Documentation

- **[Setup Guide](./docs/SETUP.md)** - Complete installation and configuration
- **[Architecture Guide](./docs/ARCHITECTURE.md)** - Technical system design
- **[API Documentation](./docs/API.md)** - Function references and examples

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### **Areas for Enhancement**
- 🌐 **Additional AI Models**: Support for Claude, GPT-4, or other language models
- 🚀 **Performance Optimization**: Parallel processing for large sites
- 🎨 **Design Templates**: Pre-built design themes and templates
- 📱 **Mobile Optimization**: Enhanced mobile-specific optimizations
- 🔍 **SEO Features**: Advanced SEO analysis and recommendations

### **Development Setup**
```bash
# Fork the repository and clone your fork
git clone https://github.com/your-username/ai-website-modernizer.git

# Create feature branch
git checkout -b feature/your-feature-name

# Make changes and test thoroughly
python -m pytest tests/  # When tests are added

# Submit pull request
```

## 📈 Roadmap

- [ ] **Multi-Model Support**: Integration with Claude, GPT-4, and other AI models
- [ ] **Template System**: Pre-built modern design templates
- [ ] **Batch Processing**: Support for multiple websites simultaneously
- [ ] **Performance Analytics**: Before/after performance comparison
- [ ] **Custom Branding**: Advanced brand guideline integration
- [ ] **API Development**: RESTful API for programmatic access

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🚀 Quick Reference

### **Key Files & Functions**
- **Main Crawler**: [`crawl_site.py:main()`](./crawl_site.py#L269) - Entry point for web crawling
- **AI Generation**: [`remake_site_with_ai.py:main()`](./remake_site_with_ai.py#L167) - AI-powered site rebuilding
- **Dashboard**: [`dashboard.py:run_full_process()`](./dashboard.py#L184) - Complete transformation pipeline
- **Content Extraction**: [`get_page_content()`](./crawl_site.py#L99) - Page data extraction logic
- **Security Validation**: [`is_safe_url()`](./crawl_site.py#L29) - SSRF protection implementation

### **Configuration Constants**
- **Crawl Limits**: [`DEFAULT_MAX_PAGES = 20`](./crawl_site.py#L19), [`DEFAULT_CRAWL_DEPTH = 2`](./crawl_site.py#L20)
- **File Names**: [`COPY_FILENAME = "copy.txt"`](./crawl_site.py#L23), [`HTML_FILENAME = "page.html"`](./crawl_site.py#L25)
- **AI Models**: Available in [`remake_site_with_ai.py`](./remake_site_with_ai.py#L170-L171)